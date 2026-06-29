# [Bug] Deadlock - 멀티스레드 상호 자원 대기로 인한 프로세스 무응답(Hang) 현상

## 1. Description (현상 설명)
* **발생 현상**: `agent-leak-app-x86` 실행 중 프로세스가 종료되지 않고 PID(Process ID)는 정상 유지되고 있으나, CPU/메모리 변화가 전혀 없고 어떠한 로그도 더 이상 찍히지 않는 **먹통(Hang)** 상태가 되었습니다.
* **발생 조건**: 멀티스레드 옵션(`MULTI_THREAD_ENABLE=true`)을 가동했을 때 발생하며, 특정 자원을 공유하는 다중 스레드 구동 환경에서 발생합니다.

## 2. Evidence & Logs (증거 자료)

### 📸 Deadlock 및 CLI 진단 스크린샷
* **스레드 자원 대기 상태 로그**:
![Deadlock](./deadlock_crash_log.png)
* **`ps -ef` 프로세스 확인 증거**:
![Deadlock ps -ef](./ps_ef_deadlock_evidence.png)
* **`ps -L` 스레드 레벨 분석 증거**:
![Deadlock ps -L](./ps_l_deadlock_evidence.png)

### 🖥️ CLI 시스템 도구 확인 증거
프로세스가 백그라운드에서 죽지 않고 유지 중이나 자원 소비율이 정체된 증거 데이터입니다.

* **PID 존재 증거** (`ps -ef | grep agent-leak-app-x86` 실행)
  ```bash
  $ ps -ef | grep agent-leak-app-x86 | grep -v grep
  agent-a+  14409  14313  0 14:51 pts/4    00:00:00 ./agent-leak-app-x86
  agent-a+  14410  14409  0 14:51 pts/4    00:00:00 ./agent-leak-app-x86
  ```
* **스레드별 리소스 변화 정체 증거** (`ps -L -p 14409` 실행)
  ```bash
  $ ps -L -p 14409
    PID   LWP TTY          TIME CMD
  14409 14409 pts/4    00:00:00 agent-leak-app-
  ```
  `ps -L -p 14409` 조회 시 단일 메인 스레드만 식별되며, 다른 작업 스레드들은 교착 상태로 인해 동작하지 않고 리소스 소비가 완전히 정체되어 있습니다.

### 📝 프로그램 실행 로그의 마지막 구간 발췌
```text
2026-06-29 13:12:11,509 [INFO] [Worker-Thread-1] Process Started. Attempting to lock [Shared_Memory_A]...
2026-06-29 13:12:11,510 [INFO] [AgentWorker][Worker-Thread-2] Process Started. Attempting to lock [Socket_Pool_B]...
2026-06-29 13:12:11,510 [INFO] [AgentWorker][Worker-Thread-1] LOCK ACQUIRED: [Shared_Memory_A]. (Holding...)
2026-06-29 13:12:11,510 [INFO] [AgentWorker] Waiting for worker threads to complete transactions...
2026-06-29 13:12:11,510 [INFO] [AgentWorker][Worker-Thread-2] LOCK ACQUIRED: [Socket_Pool_B]. (Holding...)
2026-06-29 13:12:11,511 [INFO] [AgentWorker][Worker-Thread-1] Processing critical data in Memory A...
2026-06-29 13:12:11,511 [INFO] [AgentWorker][Worker-Thread-2] Establishing network connections in Pool B...
2026-06-29 13:12:13,521 [INFO] [AgentWorker][Worker-Thread-1] Need resource [Socket_Pool_B] to finish job.
2026-06-29 13:12:13,521 [INFO] [AgentWorker][Worker-Thread-1] WAITING for [Socket_Pool_B]... (Status: BLOCKED)
2026-06-29 13:12:13,522 [INFO] [AgentWorker][Worker-Thread-2] Need resource [Shared_Memory_A] to write logs.
2026-06-29 13:12:13,527 [INFO] [AgentWorker][Worker-Thread-2] WAITING for [Shared_Memory_A]... (Status: BLOCKED)
------------------- (이후 로그 출력 무한 멈춤) -------------------
```

## 3. Root Cause Analysis (원인 분석)
* **데드락 발생 관계도 (Mermaid Diagram)**
```mermaid
graph TD
    subgraph Threads ["작업 스레드"]
        T1["Worker-Thread-1 (작업 주체 A)"]
        T2["Worker-Thread-2 (작업 주체 B)"]
    end
    subgraph Resources ["뮤텍스 자원"]
        LockA["Shared_Memory_A (뮤텍스 1)"]
        LockB["Socket_Pool_B (뮤텍스 2)"]
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
  1. **상호 배제 (Mutual Exclusion)**: 한 번에 한 스레드만 `Shared_Memory_A`와 `Socket_Pool_B`를 획득할 수 있습니다.
  2. **점유 대기 (Hold and Wait)**: `Worker-Thread-1`은 `Shared_Memory_A`를 획득한 채로 `Socket_Pool_B`를 기다리고, `Worker-Thread-2`는 `Socket_Pool_B`를 획득한 채로 `Shared_Memory_A`를 기다립니다.
  3. **비선점 (No Preemption)**: 다른 스레드가 쥐고 있는 Lock을 강제로 빼앗을 수 없습니다.
  4. **순환 대기 (Circular Wait)**: `Worker-Thread-1` -> `Socket_Pool_B` -> `Worker-Thread-2` -> `Shared_Memory_A` -> `Worker-Thread-1`로 대기 고리가 순환 구조를 이룹니다.

## 4. Workaround & Verification (조치 및 검증)
* **조치 내용**: 멀티스레드 교차 락 획득 시도를 차단하기 위해 애플리케이션의 멀티스레드 가동 플래그를 `false`로 비활성화하여 단일 스레드 순차 처리 구조로 전환했습니다.
  ```bash
  export MULTI_THREAD_ENABLE=false
  ```
* **Before & After 비교**:
  * **Before (`MULTI_THREAD_ENABLE=true`)**: 실행 후 약 10초 미만의 시간 안에 교차 점유 락 시퀀스가 실행되어 프로세스가 무응답 행(Hang) 상태에 돌입했습니다.
  * **After (`MULTI_THREAD_ENABLE=false`)**: 단일 스레드로 자원을 순차적으로 점유 및 반납하게 하여 경쟁 상태(Race Condition)를 원천 봉쇄하였고, 데드락 없이 전 과정이 정상 구동되는 것을 검증했습니다.
