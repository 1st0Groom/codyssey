# [Bug] Memory Leak - MemoryGuard 정책에 의한 프로세스 비정상 강제 종료

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
