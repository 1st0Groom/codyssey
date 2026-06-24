# 🛠️ 리눅스 프로세스 및 시스템 리소스 장애 분석 리포트 (Index)

본 저장소의 B1-2 미션은 에이전트 애플리케이션(`agent-leak-app-x86`)을 리눅스 운영 환경에서 구동하며 발생한 세 가지 대표적인 시스템 장애(Memory Leak/OOM, CPU Spike, Deadlock)의 관제 데이터와 로그를 분석하고, 환경변수를 통한 임시 조치(Workaround) 및 검증 결과를 정리한 리포트입니다.

채점 및 가독성 편의를 위해 각 장애 항목별로 기술 보고서를 개별 파일로 분리하여 구성했습니다. 아래 링크를 통해 각 리포트의 상세 내용을 확인하실 수 있습니다.

---

## 📑 장애 보고서 및 분석 자료 목차

### 1. 🚨 [Bug 01] Memory Leak / OOM Crash
* **내용**: 힙 메모리 누수로 인한 `MemoryGuard` 정책에 의한 프로세스 자가 종료 장애 분석 및 조치 결과
* **이동**: 📄 [01_Bug_OOM_Memory_Leak.md](./01_Bug_OOM_Memory_Leak.md)

### 2. ⚡ [Bug 02] CPU Spike / Watchdog Abort
* **내용**: CPU 과점유로 인한 `Watchdog` 보호 장치 가동에 따른 프로세스 강제 중단 장애 분석 및 조치 결과
* **이동**: 📄 [02_Bug_CPU_Spike.md](./02_Bug_CPU_Spike.md)

### 3. 🔒 [Bug 03] Deadlock / Unresponsive Process
* **내용**: 멀티스레드 교차 자원 획득 대기로 인한 프로세스 먹통(Hang) 현상 진단 및 조치 결과
* **이동**: 📄 [03_Bug_Deadlock.md](./03_Bug_Deadlock.md)

### 4. ⏳ [Bonus] Scheduling Algorithm Inference
* **내용**: 워커 스레드 작업 로그의 타임스탬프 패턴 분석을 통한 라운드 로빈(Round-Robin) 스케줄링 알고리즘 역추론 및 장단점 분석
* **이동**: 📄 [04_Bonus_Scheduling_Inference.md](./04_Bonus_Scheduling_Inference.md)