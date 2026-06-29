# [Analysis] 로그 패턴 분석을 통한 애플리케이션 스케줄링 알고리즘 역추론

## 1. 로그 관찰 개요
에이전트 애플리케이션의 멀티스레딩 상태에서 출력되는 개별 워커 스레드(`Thread-A`, `Thread-B`, `Thread-C`)들의 작업 패턴과 타임스탬프, 그리고 작업 진척률(Progress) 변화 추이를 수집하여 내부 런타임의 작업 스케줄링 기법을 역추적하였습니다.

## 2. 증거 로그 데이터 (App Log Snapshot)

### 📸 Scheduling Inference 로그 스크린샷
![Scheduling Inference Log](../images/scheduling_inference_log.png)

```text
2026-06-29 13:28:11,887 [INFO] [Thread-A] Task Started. Calculating... (20%)
2026-06-29 13:28:11,938 [INFO] [Thread-A] Calculating... (40%)
2026-06-29 13:28:11,988 [INFO] [Thread-A] Preempted. Progress saved at (40%)
2026-06-29 13:28:12,039 [INFO] [Thread-B] Task Started. Calculating... (20%)   <-- Thread-A 선점, Thread-B 실행 전환 (Context Switch)
2026-06-29 13:28:12,090 [INFO] [Thread-B] Calculating... (40%)
2026-06-29 13:28:12,140 [INFO] [Thread-B] Preempted. Progress saved at (40%)
2026-06-29 13:28:12,191 [INFO] [Thread-C] Task Started. Calculating... (20%)   <-- Thread-B 선점, Thread-C 실행 전환 (Context Switch)
2026-06-29 13:28:12,242 [INFO] [Thread-C] Calculating... (40%)
2026-06-29 13:28:12,292 [INFO] [Thread-C] Preempted. Progress saved at (40%)
2026-06-29 13:28:12,343 [INFO] [Thread-A] Resumed. Calculating... (60%)        <-- Thread-C 선점, Thread-A 재개
2026-06-29 13:28:12,394 [INFO] [Thread-A] Calculating... (80%)
2026-06-29 13:28:12,445 [INFO] [Thread-A] Preempted. Progress saved at (80%)
2026-06-29 13:28:12,495 [INFO] [Thread-B] Resumed. Calculating... (60%)        <-- Thread-A 선점, Thread-B 재개
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
