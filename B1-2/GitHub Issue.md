# 🛠️ [Troubleshooting Report] 리눅스 프로세스 및 시스템 리소스 장애 분석 리포트

본 리포트는 에이전트 애플리케이션(`agent-leak-app-x86`)을 리눅스 운영 환경에서 구동하며 발생한 세 가지 대표적인 시스템 장애(Memory Leak/OOM, CPU Spike, Deadlock)의 관제 데이터와 로그를 분석하고, 환경변수를 통한 임시 조치(Workaround) 및 검증 결과를 정리한 GitHub Issue 형태의 기술 보고서입니다.

---

## 📑 목차
1. [Bug 01] [Memory Leak / OOM Crash](#1-bug-01-memory-leak--oom-crash)
2. [Bug 02] [CPU Spike / Watchdog Abort](#2-bug-02-cpu-spike--watchdog-abort)
3. [Bug 03] [Deadlock / Unresponsive Process](#3-bug-03-deadlock--unresponsive-process)
4. [Bonus] [Scheduling Algorithm Inference](#4-bonus-scheduling-algorithm-inference)

---

# 1. [Bug 01] Memory Leak / OOM Crash

### 🏷️ Issue Title
`[Bug] Memory Leak - MemoryGuard 정책에 의한 프로세스 비정상 강제 종료`

---

## 1. Description (현상 설명)
* **발생 현상**: `agent-leak-app-x86` 실행 후 약 30초가 경과하자 터미널에 `SELF-TERMINATED` 메시지가 출력되며 프로세스가 예고 없이 강제 종료되었습니다.
* **발생 조건**: `MEMORY_LIMIT=256` (256MB 제한) 환경에서 구동 중 발생하였으며, 앱 내의 메모리 보호 정책인 `MemoryGuard`에 의해 모니터링 임계치를 초과한 순간 스스로를 종료시켰습니다.

## 2. Evidence & Logs (증거 자료)

### 📊 `monitor.sh` 관제 로그 (메모리 상승 추이)
관제 로그 데이터를 분석한 결과, CPU 사용량은 안정적이었으나 물리 메모리 점유율(MEM)이 초기 5%대에서 약 3초마다 선형적으로 급격히 우상향하는 패턴이 확인되었습니다.
| 타임스탬프 | 프로세스 명 | CPU 사용률 | 메모리 점유율 (MEM) | 디스크 사용량 | 방화벽 상태 |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `2026-06-22 16:18:49` | `agent-leak-app-x86` | 1.2% | **5.1%** | 9% | active |
| `2026-06-22 16:18:52` | `agent-leak-app-x86` | 1.4% | **12.4%** | 9% | active |
| `2026-06-22 16:18:55` | `agent-leak-app-x86` | 1.3% | **22.8%** | 9% | active |
| `2026-06-22 16:19:01` | `agent-leak-app-x86` | 1.4% | **48.6%** | 9% | active |
| `2026-06-22 16:19:10` | `agent-leak-app-x86` | 1.2% | **76.1%** | 9% | active |
| `2026-06-22 16:19:21` | `agent-leak-app-x86` | 1.5% | **98.2%** | 9% | active |

### 📸 OOM Crash 로그 스크린샷
![OOM Crash Log](/home/camus/workspace/codyssey/B1-2/붙여넣은 이미지.png)

<details>
<summary>📝 프로그램 실행 로그 텍스트 (클릭하여 확장)</summary>

```text
2026-06-22 16:18:49,149 [INFO] [SafetyGuard] Process priority lowered (nice=10).
2026-06-22 16:18:51,173 [INFO] [MemoryWorker] Current Heap: 25MB
2026-06-22 16:18:54,203 [INFO] [MemoryWorker] Current Heap: 50MB
2026-06-22 16:18:57,233 [INFO] [MemoryWorker] Current Heap: 75MB
2026-06-22 16:19:00,262 [INFO] [MemoryWorker] Current Heap: 100MB
2026-06-22 16:19:03,291 [INFO] [MemoryWorker] Current Heap: 125MB
2026-06-22 16:19:06,319 [INFO] [MemoryWorker] Current Heap: 150MB
2026-06-22 16:19:09,349 [INFO] [MemoryWorker] Current Heap: 175MB
2026-06-22 16:19:12,379 [INFO] [MemoryWorker] Current Heap: 200MB
2026-06-22 16:19:15,408 [INFO] [MemoryWorker] Current Heap: 225MB
2026-06-22 16:19:18,437 [INFO] [MemoryWorker] Current Heap: 250MB
2026-06-22 16:19:21,466 [INFO] [MemoryWorker] Current Heap: 275MB
2026-06-22 16:19:21,466 [CRITICAL] [MemoryGuard] Memory limit exceeded (275MB >= 256MB) / (Recommend Over 256MB)
2026-06-22 16:19:21,466 [CRITICAL] [MemoryGuard] Self-terminating process 18268 to prevent system instability.
>>> [SYSTEM] SELF-TERMINATED (Memory Limit Exceeded) <<<
```
</details>

## 3. Root Cause Analysis (원인 분석)
* **현상 분석**: 어플리케이션 내부의 `MemoryWorker` 스레드가 3초 주기로 동작하면서 약 25MB 크기의 데이터를 Heap 메모리에 할당(`malloc`)만 하고 적절히 해제(`free` 또는 GC 대상 지정)하지 못하는 전형적인 **메모리 누수(Memory Leak)** 결함이 존재합니다.
* **OS 동작 원리**: 누수된 메모리가 지속적으로 증가해 시스템 전체의 물리 메모리가 부족해지면, 리눅스 커널은 시스템 전체 불안정을 방지하고자 OOM Killer(Out of Memory Killer)를 작동시켜 프로세스를 `SIGKILL` 시그널로 강제 제거합니다. 이 프로그램은 OOM Killer에 도달하기 전, 내부 보호 프레임워크인 `MemoryGuard`가 먼저 `MEMORY_LIMIT=256` 설정을 감지하고 프로세스 자가 종료 시그널을 전송하여 예방 조치를 취했습니다.

## 4. Workaround & Verification (조치 및 검증)
* **조치 내용**: 임시 처방으로 프로그램의 생존 능력을 넓히기 위해 가용 메모리 한도를 기존 256MB에서 512MB로 상향하여 실행 환경을 수정했습니다.
  ```bash
  export MEMORY_LIMIT=512
  ```
* **Before & After 비교**:
  * **Before (`MEMORY_LIMIT=256`)**: 약 30초 만에 Heap 사용량이 275MB에 도달하여 프로세스가 즉각 강제 종료되었습니다.
  * **After (`MEMORY_LIMIT=512`)**: 임계치 완화 후 재실행 시 기존 한계점인 30초를 넘어 약 **60초** 이상 프로세스가 안정적으로 구동됨을 확인했습니다.

> [!IMPORTANT]
> `MEMORY_LIMIT`를 조정하는 것은 Crash 시점을 늦추는 임시 우회책(Workaround)일 뿐입니다. 소스코드 레벨에서 사용이 완료된 Heap 영역 객체를 메모리에서 주기적으로 비워주는 리팩토링 조치가 시급합니다.

---

# 2. [Bug 02] CPU Spike / Watchdog Abort

### 🏷️ Issue Title
`[Bug] CPU Spike - CPU 과점유 방지 정책(Watchdog)에 의한 비정상 강제 종료`

---

## 1. Description (현상 설명)
* **발생 현상**: 애플리케이션 실행 후 일정 시간이 경과하자 CPU 사용률이 급격하게 상승하고, `WATCHDOG: INITIATING EMERGENCY ABORT (SIGTERM)` 메시지와 함께 프로세스가 강제 중단되었습니다.
* **발생 조건**: 특정 워커 스레드가 CPU 자원을 과도하게 점유하자 애플리케이션 보안 감시 장치인 `Watchdog` 모듈에 의해 강제 SIGTERM 시그널이 전송되었습니다.

## 2. Evidence & Logs (증거 자료)

### 📊 `monitor.sh` 관제 로그 (CPU 급상승 추이)
메모리 사용량은 일정하게 유지되나, CPU 사용량이 초기 5%에서 순식간에 임계치 부근인 56.54%까지 비정상적으로 치솟았습니다.
| 타임스탬프 | 프로세스 명 | CPU 사용률 | 메모리 점유율 (MEM) | 디스크 사용량 | 방화벽 상태 |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `2026-06-22 18:26:02` | `agent-leak-app-x86` | **5.0%** | 4.2% | 9% | active |
| `2026-06-22 18:26:05` | `agent-leak-app-x86` | **11.4%** | 4.2% | 9% | active |
| `2026-06-22 18:26:14` | `agent-leak-app-x86` | **14.3%** | 4.2% | 9% | active |
| `2026-06-22 18:26:20` | `agent-leak-app-x86` | **25.7%** | 4.2% | 9% | active |
| `2026-06-22 18:26:30` | `agent-leak-app-x86` | **39.5%** | 4.2% | 9% | active |
| `2026-06-22 18:26:39` | `agent-leak-app-x86` | **56.5%** | 4.2% | 9% | active |

### 📸 CPU Spike Crash 로그 스크린샷
![CPU Spike Crash Log](/home/camus/workspace/codyssey/B1-2/스크린샷 2026-06-22 18-33-32.png)

<details>
<summary>📝 프로그램 실행 로그 텍스트 (클릭하여 확장)</summary>

```text
2026-06-22 18:26:02,129 [INFO] [CpuWorker] Started. Maximum CPU Limit: 95%
2026-06-22 18:26:02,129 [INFO] [CpuWorker] Current Load: 5.00%
2026-06-22 18:26:05,245 [INFO] [CpuWorker] Current Load: 11.42%
2026-06-22 18:26:08,361 [INFO] [CpuWorker] Current Load: 12.61%
2026-06-22 18:26:11,474 [INFO] [CpuWorker] Current Load: 13.54%
2026-06-22 18:26:14,590 [INFO] [CpuWorker] Current Load: 14.35%
2026-06-22 18:26:17,697 [INFO] [CpuWorker] Current Load: 16.31%
2026-06-22 18:26:20,813 [INFO] [CpuWorker] Current Load: 25.75%
2026-06-22 18:26:23,929 [INFO] [CpuWorker] Current Load: 30.60%
2026-06-22 18:26:27,041 [INFO] [CpuWorker] Current Load: 30.84%
2026-06-22 18:26:30,152 [INFO] [CpuWorker] Current Load: 39.50%
2026-06-22 18:26:33,268 [INFO] [CpuWorker] Current Load: 44.87%
2026-06-22 18:26:36,384 [INFO] [CpuWorker] Current Load: 48.96%
2026-06-22 18:26:39,499 [INFO] [CpuWorker] Current Load: 56.54%
2026-06-22 18:26:39,600 [CRITICAL] [CpuWorker] CPU Threshold Violated! (56.53999999999999%).
>>> [SYSTEM] WATCHDOG: INITIATING EMERGENCY ABORT (SIGTERM) <<<
```
</details>

## 3. Root Cause Analysis (원인 분석)
* **현상 분석**: `CpuWorker` 내부에서 무한 루프 또는 연산 처리가 비효율적으로 설계되어 있어 실행 시간이 경과함에 따라 단일 프로세스의 CPU 로드가 기하급수적으로 폭증했습니다. 
* **OS 동작 원리**: 단일 프로세스가 시스템 자원인 CPU를 과점유하면 스케줄링 대기열에 병목이 발생하여 시스템 전체의 지연(CPU Latency)이 극대화되고 다른 정상 애플리케이션들까지 무응답 상태에 빠집니다. 이를 방지하기 위해 프로그램의 자가 관제 모듈인 `Watchdog`이 미리 설정된 자원 임계치(기본설정 `CPU_MAX_OCCUPY=50`)를 위반(`56.54%` 도달)한 스레드를 감지하고, 커널에 `SIGTERM` 시그널을 발행하여 프로세스를 안전하게 종료시켰습니다.

## 4. Workaround & Verification (조치 및 검증)
* **조치 내용**: 임시 조치로서 Watchdog이 허용하는 최대 CPU 점유 허용 범위를 80%로 확대 조정해 프로세스가 CPU 로드가 높아도 바로 강제 중단되지 않도록 환경을 변경했습니다.
  ```bash
  export CPU_MAX_OCCUPY=80
  ```
* **Before & After 비교**:
  * **Before (`CPU_MAX_OCCUPY=50`)**: CPU 부하가 56.54%에 도달하는 시점(약 40초 내외)에 Watchdog이 강제 종료를 감행했습니다.
  * **After (`CPU_MAX_OCCUPY=80`)**: 허용 수준을 80%로 상향하자 동일 부하(56.54%) 환경에서도 프로세스가 예방 중단되지 않고 생존하여 작업을 안정적으로 이어감을 확인했습니다.

---

# 3. [Bug 03] Deadlock / Unresponsive Process

### 🏷️ Issue Title
`[Bug] Deadlock - 멀티스레드 상호 자원 대기로 인한 프로세스 무응답(Hang) 현상`

---

## 1. Description (현상 설명)
* **발생 현상**: `agent-leak-app-x86` 실행 중 프로세스가 종료되지 않고 PID(Process ID)는 정상 유지되고 있으나, CPU/메모리 변화가 전혀 없고 어떠한 로그도 더 이상 찍히지 않는 **먹통(Hang)** 상태가 되었습니다.
* **발생 조건**: 멀티스레드 옵션(`MULTI_THREAD_ENABLE=true`)을 가동했을 때 발생하며, 특정 자원을 공유하는 다중 스레드 구동 환경에서 발생합니다.

## 2. Evidence & Logs (증거 자료)

### 🖥️ CLI 시스템 도구 확인 증거
프로세스가 백그라운드에서 죽지 않고 유지 중이나 자원 소비율이 정체된 증거 데이터입니다.

* **PID 존재 증거** (`ps -ef | grep agent-leak-app` 실행)
  ```bash
  $ ps -ef | grep agent-leak-app | grep -v grep
  agent-ad  20134  1915  0 18:40 ?        00:00:00 ./agent-leak-app-x86
  ```
* **스레드별 리소스 변화 정체 증거** (`ps -L -p 20134` 실행)
  ```bash
  $ ps -L -p 20134 -o lwp,pcpu,pmem,stat
    LWP %CPU %MEM STAT
  20134  0.0  1.2  Sl
  20135  0.0  1.2  Sl  <-- Thread-1 (상태 정체)
  20136  0.0  1.2  Sl  <-- Thread-2 (상태 정체)
  ```
  `top -H -p 20134` 조회 시 모든 스레드가 CPU 사용률 `0.0%`로 락이 걸려 완전히 멈춰 있습니다.

### 📝 프로그램 실행 로그의 마지막 구간 발췌
```text
2026-06-22 18:40:01,102 [INFO] [Thread-1] Acquiring Lock-A...
2026-06-22 18:40:01,104 [INFO] [Thread-2] Acquiring Lock-B...
2026-06-22 18:40:01,202 [INFO] [Thread-1] Lock-A acquired. Acquiring Lock-B...
2026-06-22 18:40:01,205 [INFO] [Thread-2] Lock-B acquired. Acquiring Lock-A...
2026-06-22 18:40:02,000 [WARNING] [Thread-1] WAITING for Lock-B... (BLOCKED)
2026-06-22 18:40:02,001 [WARNING] [Thread-2] WAITING for Lock-A... (BLOCKED)
------------------- (이후 로그 출력 무한 멈춤) -------------------
```

## 3. Root Cause Analysis (원인 분석)
* **데드락 발생 관계도 (Mermaid Diagram)**
```mermaid
graph TD
    subgraph Threads ["작업 스레드"]
        T1["Thread-1 (작업 주체 A)"]
        T2["Thread-2 (작업 주체 B)"]
    end
    subgraph Resources ["뮤텍스 자원"]
        LockA["Lock-A (뮤텍스 1)"]
        LockB["Lock-B (뮤텍스 2)"]
    end

    T1 -->|1. 점유| LockA
    T2 -->|2. 점유| LockB
    T1 -.->|3. 획득 대기 (대기 상태)| LockB
    T2 -.->|4. 획득 대기 (대기 상태)| LockA

    style T1 fill:#f9f,stroke:#333,stroke-width:2px
    style T2 fill:#f9f,stroke:#333,stroke-width:2px
    style LockA fill:#bbf,stroke:#333,stroke-width:2px
    style LockB fill:#bbf,stroke:#333,stroke-width:2px
```

* **원인 분석 & OS 원리**: 
  위 로그와 관계도를 통해 **교착상태(Deadlock)**가 발생했음을 알 수 있습니다. 두 스레드가 서로 상대방이 이미 점유한 자원이 해제되기만을 기다리고 있습니다. 데드락의 4가지 성립 요건을 모두 충족합니다:
  1. **상호 배제 (Mutual Exclusion)**: 한 번에 한 스레드만 `Lock-A`와 `Lock-B`를 획득할 수 있습니다.
  2. **점유 대기 (Hold and Wait)**: `Thread-1`은 `Lock-A`를 획득한 채로 `Lock-B`를 기다리고, `Thread-2`는 `Lock-B`를 획득한 채로 `Lock-A`를 기다립니다.
  3. **비선점 (No Preemption)**: 다른 스레드가 쥐고 있는 Lock을 강제로 빼앗을 수 없습니다.
  4. **순환 대기 (Circular Wait)**: `Thread-1` -> `Lock-B` -> `Thread-2` -> `Lock-A` -> `Thread-1`로 대기 고리가 순환 구조를 이룹니다.

## 4. Workaround & Verification (조치 및 검증)
* **조치 내용**: 멀티스레드 교차 락 획득 시도를 차단하기 위해 애플리케이션의 멀티스레드 가동 플래그를 `false`로 비활성화하여 단일 스레드 순차 처리 구조로 전환했습니다.
  ```bash
  export MULTI_THREAD_ENABLE=false
  ```
* **Before & After 비교**:
  * **Before (`MULTI_THREAD_ENABLE=true`)**: 실행 후 약 10초 미만의 시간 안에 교차 점유 락 시퀀스가 실행되어 프로세스가 무응답 행(Hang) 상태에 돌입했습니다.
  * **After (`MULTI_THREAD_ENABLE=false`)**: 단일 스레드로 자원을 순차적으로 점유 및 반납하게 하여 경쟁 상태(Race Condition)를 원천 봉쇄하였고, 데드락 없이 전 과정이 정상 구동되는 것을 검증했습니다.

---

# 4. [Bonus] Scheduling Algorithm Inference

### 🏷️ Analysis Report
`[Analysis] 로그 패턴 분석을 통한 애플리케이션 스케줄링 알고리즘 역추론`

---

## 1. 로그 관찰 개요
에이전트 애플리케이션의 멀티스레딩 상태에서 출력되는 개별 워커 스레드(`Thread-A`, `Thread-B`, `Thread-C`)들의 작업 패턴과 타임스탬프, 그리고 작업 진척률(Progress) 변화 추이를 수집하여 내부 런타임의 작업 스케줄링 기법을 역추적하였습니다.

## 2. 증거 로그 데이터 (App Log Snapshot)
```text
[2026-06-22 19:00:00.100] [Thread-A] Task Started. Calculating... (10%)
[2026-06-22 19:00:00.150] [Thread-A] Calculating... (20%)
[2026-06-22 19:00:00.200] [Thread-B] Task Started. Calculating... (10%)  <-- Thread-A 중단, Thread-B 실행 전환 (Context Switch)
[2026-06-22 19:00:00.250] [Thread-B] Calculating... (20%)
[2026-06-22 19:00:00.300] [Thread-C] Task Started. Calculating... (10%)  <-- Thread-B 중단, Thread-C 실행 전환 (Context Switch)
[2026-06-22 19:00:00.350] [Thread-A] Resumed. Calculating... (30%)       <-- Thread-C 중단, Thread-A 재개
[2026-06-22 19:00:00.400] [Thread-A] Calculating... (40%)
[2026-06-22 19:00:00.450] [Thread-B] Resumed. Calculating... (30%)       <-- Thread-A 중단, Thread-B 재개
```

## 3. 패턴 분석 및 스케줄링 알고리즘 결론

### 🔍 스케줄링 패턴 분석
* **비선점형(FCFS 등) 아님**: `Thread-A`가 100% 완료되기 전에 중간에 멈추고 `Thread-B`가 CPU 자원을 할당받아 실행을 가로챘으므로 **선점형(Preemptive)** 스케줄링입니다.
* **우선순위 기반(Priority) 아님**: 특정 고우선순위 스레드가 자원을 독점하거나 긴급하게 완료되는 구조가 아니며, A -> B -> C -> A -> B 순으로 매우 평등하고 순환적인 분할 처리를 보여줍니다.
* **시간 분할(Time-Slicing) 특징**: 스레드 전환 주기가 대략 `100ms` 단위(Thread-A가 2회 실행(50ms x 2) 후 전환)로 규칙적이고 동일하게 반복 분할됩니다.

> **💡 최종 결론**:  
> 분석 데이터에 근거할 때, 본 애플리케이션의 스레드 제어 방식은 CPU 시간 할당량(Time Quantum)을 공평하게 분할해 순환 스케줄링을 돌리는 **라운드 로빈 (Round-Robin, RR) 알고리즘**입니다.

---

## 4. 라운드 로빈 알고리즘의 장단점 및 적합 아키텍처 분석

### 📈 장단점 비교

| 장점 (Advantages) | 단점 (Disadvantages) |
| :--- | :--- |
| • **공평한 자원 분배**: 아사 현상(Starvation)이 발생하지 않음.<br>• **빠른 반응성**: 모든 프로세스가 주기적으로 CPU를 할당받음.<br>• **대기 시간의 상한선**: 프로세스 개수가 $N$이고 시간 할당량이 $q$일 때 최대 대기 시간은 $(N-1)q$로 예측 가능함. | • **컨텍스트 스위칭 비용**: 스레드가 교체될 때마다 CPU 레지스터 및 캐시 메모리가 갱신되어 오버헤드가 발생함.<br>• **시간 할당량 설정 딜레마**: 시간 단위가 너무 짧으면 전환 오버헤드가 극대화되고, 너무 길면 FCFS와 다름없어져 반응성이 떨어짐. |

### 🛠️ 적합한 아키텍처 및 서비스 성격
* **적합한 아키텍처**: 실시간으로 다수의 사용자가 접속하는 **웹 서비스 서버(Web Application Server)** 및 인터랙션이 중요한 **데스크톱 GUI 환경**.
* **이유**: 개별 요청에 대해 순차 처리를 진행할 시 긴 연산 처리를 요하는 한 개의 요청이 전체 큐를 막아서 다른 사용자들의 응답 대기 시간을 늘리는 병목(Convoy Effect)이 생깁니다. 라운드 로빈은 골고루 CPU 타임을 쪼개어 응답을 돌려주므로 모든 요청자가 짧은 시간 내에 첫 응답 피드백을 받을 수 있어 사용자 경험 측면에서 압도적으로 유리합니다. (반면, 순수한 CPU 연산 처리량과 성능 극대화가 핵심인 Batch 시스템에는 컨텍스트 스위치 오버헤드가 없는 FCFS 등이 더 효율적입니다.)