# 📝 요구사항 수행 내역서 (Requirements Fulfillment Report)

---

## 🛑 [Bug] OOM Crash - 물리 메모리 누수(Memory Leak)에 의한 MemoryGuard 강제 종료

### 1. Description (현상 설명)
* **발생 현상:** `agent-leak-app`을 구동한 후 약 10분이 경과하면 별도의 경고 시스템 알림 없이 터미널에 `>>> [SYSTEM] SELF-TERMINATED (Memory Limit Exceeded) <<<` 메시지를 출력하며 프로세스가 예고 없이 돌연 다운되는 현상이 반복적으로 관측되었습니다.
* **발생 조건:** 멀티스레드 활성화 상태에서 애플리케이션의 내부 메모리 보호 정책인 `MemoryGuard` 임계치에 도달할 때 발생합니다.

### 2. Evidence & Logs (증거 자료)
* **`monitor.sh` 관제 로그 데이터:**  
  MEM 점유율이 초기 5.1%에서 시작하여 시스템 전체 부하와 관계없이 분당 선형적으로 급격히 우상향하여 종료 직전 96.8%까지 치솟는 전형적인 메모리 누수(Memory Leak) 패턴을 보입니다.

```log
[2026-05-30 14:00:00] PROCESS:agent-leak-app CPU:1.2% MEM:5.1% DISK:9% FIREWALL:active
[2026-05-30 14:03:00] PROCESS:agent-leak-app CPU:1.5% MEM:35.4% DISK:9% FIREWALL:active
[2026-05-30 14:06:00] PROCESS:agent-leak-app CPU:1.4% MEM:68.2% DISK:9% FIREWALL:active
[2026-05-30 14:09:00] PROCESS:agent-leak-app CPU:1.3% MEM:89.5% DISK:9% FIREWALL:active
[2026-05-30 14:10:00] PROCESS:agent-leak-app CPU:1.5% MEM:96.8% DISK:9% FIREWALL:active
```

* **프로그램 종료 직전 실행 로그:**

```log
[CRITICAL] [MemoryGuard] Memory limit exceeded (256MB >= 256MB) / (Recommend Over 256MB)
[CRITICAL] [MemoryGuard] Self-terminating process 25287 to prevent system instability.
>>> [SYSTEM] SELF-TERMINATED (Memory Limit Exceeded) <<<
```

### 3. Root Cause Analysis (원인 분석)
* **기술적 원인:** 애플리케이션의 특정 워커 루틴 내에서 생성된 객체나 데이터 덩어리가 사용 완료 후 힙(Heap) 메모리 영역에서 정상적으로 해제(`del` 또는 `pop`)되지 않고 지속적으로 적재되는 소스코드 결함이 존재합니다.
* **OS 동작 원리:** 프로세스의 가상 메모리 할당량이 누적되어 커널의 실제 물리 메모리 압박으로 이어지면, OS 자체 보호 메커니즘인 **OOM Killer**가 작동하여 시스템 전체가 다운되는 것을 막기 위해 프로세스를 강제 청소(`SIGKILL`)합니다. 본 앱은 OS OOM이 터지기 전 내부 `MemoryGuard` 정책을 통해 이를 선제 차단한 구조입니다.

### 4. Workaround & Verification (조치 및 검증)
* **조치 내용:** `~/.bashrc` 내에 바인딩된 가용 물리 메모리 임계값 환경변수인 `MEMORY_LIMIT` 값을 기존 `256`에서 최대 범위 수준인 `512` (MB)로 상향 조정하여 임시 버퍼 공간을 확보했습니다.
* **Before & After 비교 결과:**

| 구분 | 환경변수 설정값 | 현상 및 검증 결과 |
| :--- | :--- | :--- |
| **Before** | `MEMORY_LIMIT=256` | 기동 후 정확히 10분 시점에 메모리 고갈로 강제 종료됨. |
| **After** | `MEMORY_LIMIT=512` | 가용 메모리 증설로 인해 한계 임계점 도달 시간이 늦춰져 기존 종료 시점을 넘어서 30분 이상 안정적으로 서비스가 생존함을 팩트 체크함. |

---

## 🛑 [Bug] CPU 과점유 - 특정 워커 독점에 의한 Watchdog 긴급 Abort 장애

### 1. Description (현상 설명)
* **발생 현상:** 애플리케이션 구동 중 특정 연산 세션이 몰리는 시점에 CPU 사용률이 단일 프로세스 할당치를 초과하여 치솟다가 `WATCHDOG: INITIATING EMERGENCY ABORT` 비명과 함께 프로세스가 강제 드랍되는 현상입니다.
* **발생 조건:** 백그라운드 워커가 CPU 연산 자원을 반납하지 않고 무한 루프에 준하는 과도한 처리를 연거푸 연산할 때 발현됩니다.

### 2. Evidence & Logs (증거 자료)
* **시스템 도구(`top`) 및 관제 로그 데이터:**  
  단일 프로세스 `agent-leak-app`이 순간적으로 CPU 점유율 90% 이상을 기록하며 제피러스 시스템 전체의 CPU 컨텍스트 스위칭 지연(Latency)을 유발하는 현상이 박제되었습니다.

```log
[2026-05-30 14:15:01] PROCESS:agent-leak-app CPU:92.4% MEM:12.1% DISK:9% FIREWALL:active
```

* **프로그램 실행 로그 중 핵심 구간:**

```log
[CRITICAL] [Watchdog] CPU usage limits violated continuously. (Current: 92.4% > Limit: 40%)
[CRITICAL] [Watchdog] INITIATING EMERGENCY ABORT (SIGTERM) to protect OS scheduling layout.
>>> [SYSTEM] PROCESS ABORTED BY WATCHDOG <<<
```

### 3. Root Cause Analysis (원인 분석)
* **기술적 원인:** 멀티스레드 내부 연산 도중 정지 조건이 누락된 무한 루프 코드가 수행되었거나, 입출력(I/O) 대기 시간 동안 스레드를 슬립(`sleep`)시키지 않고 무한히 CPU 자원을 소모하며 확인하는 **Busy Waiting** 상태에 빠진 결함입니다.
* **OS 동작 원리:** 리눅스 커널의 스케줄러(CFS)는 모든 프로세스에게 공평하게 CPU 타임 슬라이스를 분배하려 하지만, 특정 프로세스가 이를 과점유하면 타 프로세스의 실행 권한이 밀리며 커널 Latency가 폭증합니다. 내부 시스템 보호 정책인 `Watchdog` 모듈이 이를 모니터링하다가 `SIGTERM` 시그널을 던져 강제 진화한 상태입니다.

### 4. Workaround & Verification (조치 및 검증)
* **조치 내용:** 환경변수 `CPU_MAX_OCCUPY` 값을 기존 `40`에서 위험 한계선인 `80` (%)으로 변경하여 프로세스가 순간적인 피크(Peak)성 연산 시점에 곧바로 차단당하지 않도록 임시 수치를 완화했습니다.
* **Before & After 비교 결과:**

| 구분 | 환경변수 설정값 | 현상 및 검증 결과 |
| :--- | :--- | :--- |
| **Before** | `CPU_MAX_OCCUPY=40` | 가벼운 연산 집중에도 40% 임계치를 넘겨 기동 후 3분 만에 Watchdog에 의해 사망. |
| **After** | `CPU_MAX_OCCUPY=80` | 임계값 상향 후 순간적인 트래픽 폭증 시점에도 시스템 보호 블록을 우회하여 무중단 관제 흐름을 유지함이 검증됨. |

---

## 🛑 [Bug] Deadlock - 멀티스레드 상호 배제 및 순환 대기에 따른 무응답(Hang) 장애

### 1. Description (현상 설명)
* **발생 현상:** 프로세스가 죽지 않고 OS 상에 버젓이 살아있으나, 분이 지나도 CPU/메모리 자원 사용량의 변화가 0으로 수렴하고 관제 스크립트와 표준 프로그램 로그 출력이 특정 지점에서 완전히 얼어버리는 무응답(Hang) 현상입니다.
* **발생 조건:** 환경변수 `MULTI_THREAD_ENABLE=true` 설정 하에 다중 스레드가 공유 자원의 락(Lock)을 교차 소유하려고 할 때 발생합니다.

### 2. Evidence & Logs (증거 자료)
* **PID 존재 증거 (`ps -ef`):**

```bash
$ ps -ef | grep agent-leak-app
agent-ad  25287  24110  0 14:20 ?        00:00:00 ./agent-leak-app
```
*(프로세스는 SIGKILL을 맞지 않고 메모리상에 명확히 25287로 상주하고 있음)*

* **스레드별 자원 변화 정체 증거 (`top -H`):**

```bash
$ top -H -p 25287
  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
25288 agent-ad  20   0  125M   32M  11M S   0.0   0.3   0:00.00 worker-thread-A
25289 agent-ad  20   0  125M   32M  11M S   0.0   0.3   0:00.00 worker-thread-B
```
*(모든 서브 워커 스레드의 %CPU 수치가 0.0%에서 미동도 하지 않는 정체 상태 확인)*

* **프로그램 실행 로그의 마지막 데드라인 기록:**

```log
[INFO] [Thread-A] Attempting to acquire Lock-Y... (Currently holding Lock-X)
[INFO] [Thread-B] Attempting to acquire Lock-X... (Currently holding Lock-Y)
[DEBUG] [Thread-A] STATUS: WAITING... STATUS: BLOCKED
[DEBUG] [Thread-B] STATUS: WAITING... STATUS: BLOCKED
```

### 3. Root Cause Analysis (원인 분석)
* **기술적 원인:** 스레드 A는 락 X를 쥔 채 락 Y를 요구하고, 스레드 B는 락 Y를 쥔 채 락 X를 요구하는 **순환 대기(Circular Wait)** 구조가 형성되었습니다. 교착상태의 4대 조건인 상호 배제, 점유 대기, 비선점, 순환 대기가 완벽히 충족되어 서로 상대방의 열쇠가 풀리기만을 무한히 기다리는 전형적인 데드락(Deadlock) 결함입니다.
* **OS 동작 원리:** 커널 수준에서 두 스레드는 모두 `Futex` 대기 큐에 잠기며 Task State가 `D` 상태 혹은 `S` 상태로 대기하게 됩니다. OS는 이 상태를 스스로 풀 수 없으므로 외부에서 강제로 프로세스를 종료하기 전까지 영원히 자원을 소모한 채 무응답 상태를 유지합니다.

### 4. Workaround & Verification (조치 및 검증)
* **조치 내용:** 멀티스레드 동시성 로직을 우회하기 위해 환경변수 `MULTI_THREAD_ENABLE` 값을 `false`(또는 `0`)로 전면 수정하여 단일 스레드로 안전하게 순차 처리하도록 환경을 고정했습니다.
* **Before & After 비교 결과:**

| 구분 | 환경변수 설정값 | 현상 및 검증 결과 |
| :--- | :--- | :--- |
| **Before** | `MULTI_THREAD_ENABLE=true` | 교차 락 획득 시점 진입과 동시에 데드락 발생, 관제 시스템 전면 먹통. |
| **After** | `MULTI_THREAD_ENABLE=false` | 단일 스레드가 자원을 순차적으로 독점 점유 및 확실히 해제하며 실행되므로 교착 상태의 근본 조건인 '순환 대기'가 파괴되어 무응답 행 현상이 완벽히 회피됨을 최종 실증함. |

---

## 📊 [Analysis] 로그 패턴 분석을 통한 스케줄링 알고리즘 역추론 리포트 (Bonus)

### 1. 로그 관찰 개요
`agent-leak-app`이 정상 컨디션에서 작동할 때 뿜어내는 다중 워커 스레드들의 타임스탬프와 태스크 진행률(Progress) 데이터 간의 교차 빈도를 정밀 계측하여, 현재 내부 엔진 및 운영체제 레이어에 탑재된 스케줄링 기법을 역추적했습니다.

### 2. 증거 자료 및 패턴 분석

```log
[2026-05-30 15:00:00.100] [Thread-A] Task Started. Calculating... (10%)
[2026-05-30 15:00:00.150] [Thread-A] Calculating... (20%)
[2026-05-30 15:00:00.200] [Thread-B] Task Started. Calculating... (10%)  <-- Thread-A 일시 중단, B 강제 진입
[2026-05-30 15:00:00.250] [Thread-B] Calculating... (20%)
[2026-05-30 15:00:00.300] [Thread-C] Task Started. Calculating... (10%)  <-- Thread-B 일시 중단, C 강제 진입
[2026-05-30 15:00:00.350] [Thread-A] Resumed. Calculating... (30%)       <-- Thread-A 자원 재할당 및 복귀
```

* **순차 처리(FCFS) 기각 근거:** `Thread-A`가 진행률 100%를 달성하여 완료 보고를 던지기 전에 `Thread-B`와 `Thread-C`가 중간에 끼어들어 자원을 선점하는 현상이 명확히 포착되었습니다. 따라서 **비선점형 방식**은 배제됩니다.
* **우선순위(Priority) 기각 근거:** 특정 스레드가 고유 권한으로 CPU를 계속 독점하거나 비대칭적으로 연산 속도가 치솟는 경향성 없이, 모든 스레드가 공평하게 **50ms 단위**로 CPU 클럭을 번갈아 나누어 갖는 대칭성 패턴이 도출되었습니다.

### 3. 최종 결론 및 아키텍처 분석
* **최종 도출 알고리즘:** 각 스레드마다 균등한 **시간 할당량(Time Quantum)**을 부여하고, 시간이 만료되면 타이머 인터럽트를 통해 문맥 교환(Context Switching)을 강제하는 **라운드 로빈(Round-Robin) 스케줄링 알고리즘**으로 최종 추론됩니다.
* **기술적 장단점:**
  * **장점:** 모든 태스크가 최소한의 자원 분배를 보장받으므로 기아 현상(Starvation)이 발생하지 않으며, 응답성(Response Time)이 극도로 짧아집니다.
  * **단점:** 스레드가 많아질수록 문맥 교환에 따른 CPU 오버헤드가 누적되어 실제 순수 연산의 처리량(Throughput)이 저하될 수 있습니다.
* **적합한 서비스 아키텍처:** 대규모 연산을 밀어붙이는 배치 처리 서버보다는 사용자 간의 균등하고 빠른 인터랙션 및 실시간 패킷 응답이 생명인 엔터프라이즈급 웹 서버(Nginx 등) 및 API 서비스 환경에 가장 최적화된 구조입니다.