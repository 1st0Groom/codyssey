# 🚀 Linux-Based Agent Application Infrastructure & Automation Project

본 프로젝트는 ROG Zephyrus G14(Ubuntu 환경)에서 다중 계정 격리 보안 구조를 설계하고, 백그라운드 서비스 에이전트 구동 및 이를 실시간 관제하기 위한 시간 기반 자동화 쉘 스크립트(`monitor.sh`)와 로그 보존 정책을 완수한 인프라 엔지니어링 미션입니다.

---

## 🏗️ 1. 시스템 아키텍처 및 권한 설계 (Directory & Permission)

리눅스의 최소 권한 원칙(Principle of Least Privilege)과 사용자 격리 정책을 기반으로 디렉토리 및 파일 권한을 매칭했습니다.

### 👥 계정 및 그룹 설계
* **관리자 계정:** `camus` (수동 인프라 튜닝 및 `sudo` 마스터 계정)
* **어드민(서비스) 계정:** `agent-admin` (에이전트 앱 소유 및 크론탭 실행 주체)
* **개발자 계정:** `agent-dev` (관제 스크립트 소유 및 수동 디버깅 주체)
* **관리 그룹:** `agent-core` (어드민과 개발자가 상호 협업 및 로그 공유를 위해 소속된 핵심 그룹)
* **공동 그룹:** `agent-common` (공용 업로드 공간 제어를 위한 일반 그룹)

### 📁 디렉토리 계층 구조 및 권한 현황
| 절대 경로 | 소유자 (Owner) | 그룹 (Group) | 기본 권한 (Perm) | 설명 |
| :--- | :--- | :--- | :--- | :--- |
| `/home/agent-admin/agent-app/` | `agent-admin` | `agent-core` | `755` | 인프라 메인 홈 |
| `└── agent_app` | `agent-admin` | `agent-core` | `755` | 에이전트 유닉스 실행 파일 |
| `└── api_keys/secret.key` | `agent-admin` | `agent-core` | `600` | 보안 API 키 (소유자 독점 권한) |
| `└── bin/monitor.sh` | `agent-dev` | `agent-core` | `750` | 관제 스크립트 (개발자 소유, 그룹 실행) |
| `└── upload_files/` | `agent-admin` | `agent-common` | `770` | 데이터 업로드 협업 공간 |
| `/var/log/agent-app/` | `agent-admin` | `agent-core` | `770` | 실시간 수집 및 관제 로그 저장소 |
| `/var/log/monitor/agent-app/archive/` | `agent-admin` | `agent-core` | `775` | [보너스] 7일 경과 로그 압축 보존소 |

---

## 🛠️ 2. 핵심 구현 기능

### 1) Agent Boot Sequence 완수
환경 변수 정의 및 `secret.key` 팩트 매칭을 완료하여 부트 체크 5단계 전원 `[OK]` 도장 및 `Agent READY` 바인딩을 성공시켰습니다.
* **서비스 포트:** `15034` (LISTEN 상태 유지)

### 2) 관제 자동화 (`monitor.sh`)
`agent-dev` 소유의 쉘 스크립트가 임계값(`CPU 20%`, `MEM 10%`, `DISK 80%`)을 실시간 추적하여 표준 포맷 로그를 누적합니다.
* **프로세스 추적 치트키:** 크론탭 백그라운드 환경 미스매치를 방지하기 위해 정밀 타격 명령어(`pidof`) 적용.
* **크론탭 스케줄러:** `agent-admin` 명의로 1분마다 무중단 자동 실행 등록 (`* * * * *`)

### 3) [보너스] 시간 기반 로그 보존 정책 (Log Rotation)
디스크 용량 고갈 방지를 위해 예외 처리가 완벽히 포함된 정리 로직을 가동합니다.
* **7일 경과:** `/var/log/agent-app/*.log` 대상을 `gzip` 압축 아카이브 후 원본 삭제 처리.
* **30일 경과:** `archive/*.gz` 구버전 파일 추적 후 디스크에서 영구 삭제.
* **안전 철벽 예외 처리:** 아카이브 디렉토리 미존재 시 자동 생성, 권한 부족 시 `[CRITICAL]` 로그 생성 후 안전 종료(`exit 1`), 대상 파일 0개 시 에러 없이 `Skipped` 처리.

---

## 📊 3. 최종 인프라 가동 로그 증적 (Verification)

### 🟢 서비스 데몬 백그라운드 구동 확인
```bash
$ ps -ef | grep agent_app
agent-ad  25287  24110  0 15:14 ?        00:00:02 ./agent_app