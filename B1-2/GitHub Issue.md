[Bug] {장애 유형} - {한 줄 요약}

## 1. Description (현상 설명)
* **발생 현상:** `agent-leak-app-x86` 실행 후 약 30초가 경과하자 터미널에 `SELF-TERMINATED` 메시지가 출력되며 프로세스가 예고 없이 강제 종료(Killed)되었습니다. 
* **발생 조건:** `MEMORY_LIMIT=256`인 환경에서 앱 내부의 `MemoryGuard` 시스템이 메모리 점유율을 모니터링하던 중 발생했습니다.

## 2. Evidence & Logs (증거 자료)
프로세스 실행 로그 분석 결과, `MemoryWorker` 스레드가 3초마다 약 25MB씩 지속적으로 Heap 메모리를 할당하는 패턴이 관측되었습니다. 

```text
[ Application Log Snapshot ]
2026-06-22 16:18:49,149 [INFO] [SafetyGuard] Process priority lowered (nice=10).
...
2026-06-22 16:18:51,173 [INFO] [MemoryWorker] Current Heap: 25MB
2026-06-22 16:18:54,203 [INFO] [MemoryWorker] Current Heap: 50MB
2026-06-22 16:19:00,262 [INFO] [MemoryWorker] Current Heap: 100MB
...
2026-06-22 16:19:18,437 [INFO] [MemoryWorker] Current Heap: 250MB
2026-06-22 16:19:21,466 [INFO] [MemoryWorker] Current Heap: 275MB
2026-06-22 16:19:21,466 [CRITICAL] [MemoryGuard] Memory limit exceeded (275MB >= 256MB)
2026-06-22 16:19:21,466 [CRITICAL] [MemoryGuard] Self-terminating process 18268 to prevent system instability.
>>> [SYSTEM] SELF-TERMINATED (Memory Limit Exceeded) <<<


## 3. Root Cause Analysis (원인 분석)
기술적 원인: 어플리케이션 내부에 메모리를 할당(malloc)하기만 하고 해제(free/Garbage Collection)하지 않는 메모리 누수(Memory Leak) 결함이 존재합니다.

OS 동작 원리: 물리 메모리 누수가 지속되면 시스템 전체의 OOM(Out of Memory) 상태를 유발하여 커널 패닉을 일으킬 수 있습니다. 이를 방지하기 위해 앱 내부의 MemoryGuard 로직이 환경변수(MEMORY_LIMIT=256) 임계치를 초과(275MB)한 순간 스스로 자신에게 SIGKILL(Killed) 시그널을 보내 시스템 보호 조치를 취한 것입니다.

## 4. Workaround & Verification (조치 및 검증)
조치 내용: ~/.bashrc에 설정된 가용 메모리 상한 임계치를 기존 256MB에서 권장 수치 이상인 512MB로 상향 조정했습니다. (export MEMORY_LIMIT="512")

검증 결과 (Before & After):

Before: MEMORY_LIMIT=256 일 때 실행 후 약 30초 만에 강제 종료됨.

After: MEMORY_LIMIT=512 상향 후 실행 시 프로세스 생존 시간이 유의미하게 연장됨 (약 1분 생존 확인).

추가 제안: 환경변수 상향은 OOM 발생 시점을 늦추는 임시 방편(Workaround)일 뿐입니다. 근본적 해결을 위해 메모리를 반납하지 않는 소스코드 레벨의 결함 패치가 시급합니다.


[두 번쨰 과제 제출용]
# [Bug] Deadlock - 멀티스레드 환경 자원 순환 대기(Circular Wait)로 인한 무응답 현상

## 1. Description (현상 설명)
* **발생 현상:** `agent-leak-app-x86` 실행 후 메모리 누수로 인한 강제 종료는 발생하지 않았으나, 실행 직후 특정 시점부터 프로세스가 종료되지도 않은 채 완전히 멈춰버렸습니다. CPU나 물리 메모리의 변화율은 0%에 수렴하며, 애플리케이션의 진행 로그 출력도 완전히 중단된 무응답 상태입니다.
* **발생 조건:** 스레드 동시성 처리가 활성화된 `MULTI_THREAD_ENABLE="true"` 환경에서 발생했습니다.

## 2. Evidence & Logs (증거 자료)
터미널에서 애플리케이션 진행 로그가 멈춘 마지막 지점을 확인한 결과, 두 스레드가 서로의 자원을 대기하며 블록된 상태를 확인했습니다. (현재 다른 터미널 창에서 `ps -ef | grep agent-leak-app` 입력 시 프로세스가 살아있음이 증명됨)

```text
[ Application Log Snapshot ]
2026-06-22 18:04:11,263 [INFO] [Worker-Thread-1] LOCK ACQUIRED: [Shared_Memory_A]. (Holding...)
2026-06-22 18:04:11,263 [INFO] [Worker-Thread-2] LOCK ACQUIRED: [Socket_Pool_B]. (Holding...)
...
2026-06-22 18:04:13,266 [INFO] [Worker-Thread-2] WAITING for [Shared_Memory_A]... (Status: BLOCKED)
2026-06-22 18:04:13,274 [INFO] [Worker-Thread-1] WAITING for [Socket_Pool_B]... (Status: BLOCKED)

3. Root Cause Analysis (원인 분석)
기술적 원인: 전형적인 교착상태(Deadlock) 결함입니다.

OS 동작 원리 분석: Thread-1과 Thread-2가 각각 자원을 점유한 상태에서 상대방의 자원을 요구하는 점유 대기(Hold and Wait) 및 순환 대기(Circular Wait) 조건이 성립되었습니다. 스레드 로직 내에 타임아웃(Timeout)이나 자원 선점(Preemption) 기능이 구현되어 있지 않아 영구적인 교착상태에 빠진 것입니다.

4. Workaround & Verification (조치 및 검증)
조치 내용: ~/.bashrc의 환경변수를 수정하여 멀티스레드 동시성 모드를 해제하고 단일 스레드 모드로 강제 전환했습니다. (export MULTI_THREAD_ENABLE="false")

검증 결과 (Before & After):

Before: MULTI_THREAD_ENABLE="true" 시 프로세스가 무응답 상태에 빠짐.

After: MULTI_THREAD_ENABLE="false" 적용 시 동시 접근에 의한 자원 경합이 원천 차단되어 데드락 현상이 회피될 것으로 예상됨.

추가 제안: 환경변수를 통한 단일 스레드 전환은 성능 저하를 유발합니다. 근본적 해결을 위해 개발팀은 스레드의 자원 획득 순서를 한 방향으로 통일시키거나, Mutex Lock 획득 시 타임아웃을 설정하는 방식으로 코드를 리팩토링해야 합니다.

.

📝 [CPU Spike] GitHub Issue 리포트 작성 가이드
이 내용을 복사해서 세 번째 필수 과제로 제출하시면 됩니다.

Markdown
# [Bug] CPU 과점유 방지 정책(Watchdog) 발동에 의한 프로세스 강제 종료

## 1. Description (현상 설명)
* **발생 현상:** `agent-leak-app-x86` 실행 후 일정 시간이 경과함에 따라 애플리케이션의 CPU 사용률이 급격히 상승했습니다. 이후 터미널에 `[SYSTEM] WATCHDOG: INITIATING EMERGENCY ABORT (SIGTERM)` 메시지가 출력되며 프로세스가 시스템에 의해 강제 종료되었습니다.
* **발생 조건:** 애플리케이션의 허용 CPU 부하 한계치인 `CPU_MAX_OCCUPY`를 95%로 상향 설정하여 실행했을 때 발생했습니다.

## 2. Evidence & Logs (증거 자료)
터미널 로그 분석 결과, `CpuWorker`가 점유하는 CPU 로드율이 초기 5%에서 시작하여 약 40초 만에 56.54%까지 비정상적으로 치솟는 스파이크(Spike) 패턴이 관측되었습니다.

```text
[ Application Log Snapshot ]
2026-06-22 18:26:00,119 [INFO] Agent Initiate : Limit: 95% [ WARNING: Recommend Under 50% ]
...
2026-06-22 18:26:27,041 [INFO] [CpuWorker] Current Load: 30.84%
2026-06-22 18:26:30,152 [INFO] [CpuWorker] Current Load: 39.50%
2026-06-22 18:26:36,384 [INFO] [CpuWorker] Current Load: 48.96%
2026-06-22 18:26:39,499 [INFO] [CpuWorker] Current Load: 56.54%
2026-06-22 18:26:39,600 [CRITICAL] [CpuWorker] CPU Threshold Violated! (56.53999999999999%).
>>> [SYSTEM] WATCHDOG: INITIATING EMERGENCY ABORT (SIGTERM) <<<
3. Root Cause Analysis (원인 분석)
기술적 원인: 특정 프로세스(CpuWorker)가 로직 결함 또는 무한 루프로 인해 CPU 자원을 과도하게 점유하는 CPU 스파이크(Spike) 장애입니다.

OS 및 Watchdog 동작 원리: 단일 프로세스의 CPU 과점유는 시스템 전체의 지연(Latency)과 다른 프로세스의 기아(Starvation) 현상을 유발합니다. 이를 막기 위해 애플리케이션 내부의 감시 프로세스인 Watchdog이 권장 임계치(50%)를 초과하는 비정상적인 CPU 폭주를 감지하고, 프로세스 스스로에게 SIGTERM 시그널을 보내 즉각적으로 종료시키는 안전 조치를 취한 것입니다.

4. Workaround & Verification (조치 및 검증)
조치 내용: ~/.bashrc의 환경변수 CPU_MAX_OCCUPY 값을 Watchdog 권장 수치인 50% 미만(기본값 40%)으로 원복 조치했습니다. (export CPU_MAX_OCCUPY="40")

검증 결과 (Before & After):

Before: CPU_MAX_OCCUPY="95" 설정 시 56% 구간에서 Watchdog에 의해 강제 종료됨.

After: CPU_MAX_OCCUPY="40" 설정 시 CPU 부하가 10% 도달 후 쿨다운(Cooldown) 과정을 거치며 강제 종료 없이 프로세스가 안정적으로 유지됨.

추가 제안: 현재는 Watchdog이 셧다운을 통해 방어하고 있으나, 개발팀은 CpuWorker 로직 내부에 불필요한 연산이 집중되는 구간(Bottleneck)이 없는지 프로파일링하고 sleep() 또는 비동기 처리를 도입해야 합니다.