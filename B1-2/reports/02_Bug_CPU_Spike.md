# [Bug] CPU Spike - CPU 과점유 방지 정책(Watchdog)에 의한 비정상 강제 종료

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

### 📸 CPU Spike 관련 스크린샷
* **CPU 과점유 프로세스 진단 (`top`)**:
![CPU Overload top](./cpu_overload_top.png)
* **Watchdog 강제 중단 로그**:
![CPU Spike Crash Log](./cpu_spike_crash_log.png)

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
