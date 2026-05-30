# 🚀 Linux-Based Agent Application Infrastructure & Automation Project

본 프로젝트는 Ubuntu 22.04 LTS 환경에서 다중 사용자 격리 보안 체계를 설계하고, 백그라운드 서비스 에이전트 구동 및 이를 무중단으로 실시간 관제하기 위한 시간 기반 자동화 쉘 스크립트(`monitor.sh`)와 로그 관리 정책을 완수한 인프라 엔지니어링 미션입니다.

---

## 🏗️ 1. 인프라 구조 및 권한 설계 (Evaluation 1, 2, 3)

### 📁 디렉토리 계층 구조 및 권한 매칭 현황
리눅스의 **최소 권한 원칙(Principle of Least Privilege)**에 따라 파일시스템 격리 정책을 강제 적용했습니다.

| 절대 경로 | 소유자 (Owner) | 그룹 (Group) | 권한 (Perm) | 권한 설정 명령어 및 엔지니어링 의미 |
| :--- | :--- | :--- | :--- | :--- |
| `/home/agent-admin/agent-app/` | `agent-admin` | `agent-core` | `755` | `sudo chmod 755 [경로]` / 외부 계정의 진입(`x`) 및 조회(`r`) 허용 |
| `├── agent_app` | `agent-admin` | `agent-core` | `755` | `sudo chmod 755 [파일]` / 에이전트 유닉스 바이너리 실행 권한 부여 |
| `├── api_keys/secret.key` | `agent-admin` | `agent-core` | `600` | `sudo chmod 600 [파일]` / **보안 디렉토리**. 소유자 외 읽기/쓰기 절대 차단 |
| `└── bin/monitor.sh` | `agent-dev` | `agent-core` | `750` | `sudo chmod 750 [파일]` / **개발자 소유, 어드민 그룹 실행**. 외부 계정 차단 |
| `└── upload_files/` | `agent-admin` | `agent-common` | `770` | `sudo chmod 770 [경로]` / **공유 디렉토리**. `agent-common` 그룹 내 R/W 협업 |
| `/var/log/agent-app/` | `agent-admin` | `agent-core` | `770` | `sudo chmod 770 [경로]` / 실시간 관제 로그 저장소. 그룹 내 수정 권한 보장 |
| `/var/log/monitor/agent-app/archive/` | `agent-admin` | `agent-core` | `775` | `sudo chmod 775 [경로]` | [보너스 2] 시간 기반 로그 보존 정책 아카이브 공간 |

### 👥 계정 및 그룹 구성 현황
* **`agent-admin`**: 운영/관리 및 크론탭 실행 주체 (`agent-common`, `agent-core` 소속)
* **`agent-dev`**: 개발/운영 및 `monitor.sh` 작성자 (`agent-common`, `agent-core` 소속)
* **`agent-test`**: QA/테스트 수행 계정 (`agent-common` 소속)

---

## 🛡️ 2. 핵심 보안 및 네트워크 설정 (Evaluation 1, 3)

### 1) SSH 포트 변경 및 Root 원격 접속 차단
* **설정 파일 경로**: `/etc/ssh/sshd_config`
* **적용 명령어**:
  ```bash
  sudo sed -i 's/#Port 22/Port 20022/' /etc/ssh/sshd_config
  sudo sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config
  sudo systemctl restart sshd
인프라 검증 명령어:

Bash
ss -tulnp | grep sshd   # 포트 20022 LISTEN 상태 팩트 체크
2) 방화벽(UFW) 최소 개방 정책
인바운드 트래픽을 엄격히 통제하여 공격 표면(Attack Surface)을 최소화했습니다.

적용 명령어:

Bash
sudo ufw default deny inbound
sudo ufw allow 20022/tcp  # SSH 포트 허용
sudo ufw allow 15034/tcp  # APP 서비스 포트 허용
sudo ufw enable
인프라 검증 명령어:

Bash
sudo ufw status verbose   # 20022, 15034 외 전면 차단 확인
🚀 3. 애플리케이션 구동 및 자동 관제 구현 (Evaluation 1, 2, 3)
1) 에이전트 서비스 환경 변수 및 Boot Sequence 완수
agent-admin 계정의 ~/.bashrc에 고정 실행 환경 변수를 주입하고 바이너리를 가동했습니다.

배포 및 기동 명령어:

Bash
# agent-admin 계정으로 실행
cd /home/agent-admin/agent-app
nohup ./agent_app > /var/log/agent-app/app_init.log 2>&1 &
2) 시스템 관제 자동화 스크립트 (monitor.sh)
위치: /home/agent-admin/agent-app/bin/monitor.sh

크론탭 등록 (crontab -e):

코드 스니펫
* * * * * /home/agent-admin/agent-app/bin/monitor.sh
3) [보너스 2] 시간 기반 로그 보존 정책 (Log Rotation)
디스크 임계치 고갈을 방지하기 위해 예외 처리가 유기적으로 결합된 로직을 Bash 스크립트 내에 완전 내장했습니다.

7일 경과: /var/log/agent-app/*.log 대상 gzip 압축 후 아카이브 이동 및 원본 안전 삭제 (rm -f).

30일 경과: archive/*.gz 추적 후 디스크 영구 삭제.

예외 처리: 아카이브 디렉토리 미존재 시 자동 생성(mkdir -p), 권한 부족 시 [CRITICAL] 로그 생성 후 안전 종료(exit 1), 대상 파일 0개 시 에러 없이 Skipped 처리.

🕵️‍♂️ 4. 평가 문항 핵심 지표 증적 자료 (Artifacts)
🟢 증적 1: 에이전트 앱 Boot Sequence 5단계 전원 [OK] 통과
Plaintext
>>> Starting Agent Boot Sequence...
[1/5] Checking User Account               [OK]
   ... Running as service user 'agent-admin' (uid=1001)
[2/5] Verifying Environment Variables     [OK]
   ... All required Envs correct
[3/5] Checking Required Files             [OK]
   ... Verified 'secret.key' with correct key string.
[4/5] Checking Port Availability          [OK]
   ... Port 15034 is available.
[5/5] Verifying Log Permission            [OK]
   ... Log directory is writable: /var/log/agent-app
------------------------------------------------------------
All Boot Checks Passed!
Agent READY
🟢 증적 2: 관제 스크립트에 의한 실시간 수집 및 보존 로그 (monitor.log)
tail -f /var/log/agent-app/monitor.log 구동 결과, 1분 주기로 무중단 자동 누적되는 팩트 데이터입니다. 앱의 시뮬레이션 로직에 따라 자원 임계치 초과 시 경고가 정상 트리거됩니다.

Plaintext
[2026-05-30 15:30:01] PID:25287 CPU:5% MEM:31% DISK_USED:9%
[2026-05-30 15:30:01] [WARNING] MEM threshold exceeded! (Current: 31%)
[2026-05-30 15:30:01] [INFO] No logs older than 7 days found. Compression skipped.
[2026-05-30 15:31:01] PID:25287 CPU:12% MEM:36% DISK_USED:9%
[2026-05-30 15:31:01] [WARNING] MEM threshold exceeded! (Current: 36%)
[2026-05-30 15:31:01] [INFO] No logs older than 7 days found. Compression skipped.
🧠 5. 엔지니어링 인터뷰 및 이론적 근거 (Evaluation 2, 3, 4)
Q1. SSH 포트 변경 및 Root 접속 차단이 왜 위협 모델 관점에서 효과적인가?
답변: 인터넷에 노출된 서버는 무차별 대입 공격(Brute Force Attack)과 자동화된 스캐닝 봇의 상시적인 표적이 됩니다. 봇들은 기본 포트인 22번을 타격하고 최고 권한자인 root 계정 탈취를 시도합니다. 포트를 20022로 바꾸는 것만으로도 단순 스캐닝 타격 대상에서 99% 제외(Security through obscurity)되며, PermitRootLogin no 설정을 통해 설령 패스워드가 노출되더라도 외부 가상 단말을 통한 최고 권한으로의 다이렉트 진입 경로를 원천 차단할 수 있습니다.

Q2. api_keys와 로그 디렉토리를 agent-core 그룹으로 제한한 이유는 무엇인가?
답변: 최소 권한 원칙(Principle of Least Privilege)에 따른 설계입니다. 테스트 계정(agent-test)이나 일반 외부 프로세스는 서비스의 핵심 인증 자산인 secret.key를 읽을 필요가 없으며, 시스템 내부 관제 로그를 수정하거나 파괴할 권한이 주어져서는 안 됩니다. 따라서 핵심 인프라를 제어하는 agent-admin과 agent-dev만 agent-core 그룹으로 묶어 해당 영역의 R/W 권한을 독점케 함으로써 내부 위협 및 권한 상승 공격을 방어합니다.

Q3. 관제 스크립트 내부에서 사용한 핵심 명령어의 선택 이유는 무엇인가?
답변:

프로세스 식별 (pidof): pgrep -f는 스크립트 경로에 포함된 문자열까지 오탐지하여 크론탭 환경에서 혼선을 줄 우려가 큽니다. 반면 pidof는 Linux 커널 순수 매칭을 통해 정확히 바이너리 명칭(agent_app)을 가진 PID만 정밀 타격하므로 백그라운드 관제에 가장 안전합니다.

포트 확인 (ss -tuln): 기존 netstat은 무겁고 느리며 최신 리눅스 패키지에서 Deprecated 추세입니다. ss 명령어는 커널의 넷링크(Netlink) 인터페이스를 직접 호출하므로 소켓 상태 파악 속도가 압도적으로 빠르고 효율적입니다.

Q4. CPU/MEM/DISK 자원 추출 방식과 리다이렉션 기호(>, >>)의 차이는?
답변:

자원 파싱: top -bn1을 사용해 CPU Idle 값을 구한 뒤 100 - idle 수식으로 정확한 순간 사용률을 연산했습니다. 메모리는 free 명령어의 전체 대비 사용량 비율을 awk로 소수점 파싱했습니다. 디스크는 df / 결과의 5번째 필드를 파싱했습니다.

리다이렉션 차이: > 기호는 기존 파일 내용을 완전히 지우고 새로 쓰는 덮어쓰기(Overwrite)이며, >> 기호는 기존 내용 뒤에 새로운 데이터를 붙여나가는 추가(Append)입니다. 히스토리성 유지를 통해 장애 시점의 전후 맥락을 추적해야 하는 시스템 모니터링 로그 인프라에는 반드시 데이터 보존을 위해 >> 기호를 사용해야 합니다.

Q5. "경고는 출력하되 종료하지 않는 항목"을 분리한 운영상의 이유는?
답변: 에이전트 서비스의 중단 여부를 결정짓는 핵심 지표(프로세스 다운, 포트 미개방)는 시스템 관점의 Critical Failure이므로 즉시 스크립트를 exit 1로 종료해 관제 센터에 긴급 알람을 쳐야 합니다. 반면, 방화벽 비활성화나 단순 자원 임계치 초과(예: CPU > 20%)는 현재 서비스 자체는 정상 동작 중인 상태입니다. 이를 오류로 처리해 스크립트를 종료해버리면 후속 관제 및 로그 수집이 통째로 중단되는 운영 마비가 발생하므로, Warning으로 로그만 남기고 모니터링 흐름을 유지하는 것이 정석입니다.

Q6. 모니터링 대상이 웹 서버(Nginx)로 바뀐다면 변경해야 할 포인트는?
답변:

프로세스 명: agent_app에서 nginx 마스터 프로세스 추적으로 변경.

포트: TCP 15034에서 웹 표준 포트인 TCP 80 (HTTP) 또는 443 (HTTPS) 청취 상태 확인으로 변경.

임계값 및 로그: 웹 서버 특성상 대규모 트래픽 처리가 빈번하므로 기본 CPU/MEM 경고 임계값을 상향 조정(예: CPU > 70%)하고, 커넥션 풀 고갈을 감시하기 위한 Active Connections 카운트 수집 로직을 추가해야 합니다.

Q7. "프로세스는 살아있는데 포트가 안 열리는 상황" 발생 시 원인 후보와 확인 순서는?
답변:

원인 후보: 1) 애플리케이션 내부 소켓 바인딩 코드 에러 (Deadlock 또는 무한 루프), 2) 잘못된 네트워크 인터페이스 바인딩 (예: 127.0.0.1로 묶여 외부 접근 불가능), 3) 포트 중복 점유로 인한 바인딩 실패.

확인 순서:

sudo netstat -lnp | grep [포트] 또는 ss 명령어로 해당 포트를 다른 고스트 프로세스가 쥐고 있는지 먼저 확인합니다.

앱 자체 초기화 로그(cat /var/log/agent-app/app_init.log)를 열어 소켓 바인딩 실패 에러 메시지(예: Address already in use)가 찍혔는지 팩트 체크합니다.

strace -p [PID] 명령어를 통해 해당 프로세스가 어떤 시스템 콜에서 멈춰있는지 추적합니다.

Q8. 로그 급증으로 디스크 고갈 위기 시 운영자가 취할 대응책은?
답변:

단기 대응 (긴급 조치): sudo tail로 불필요한 디버그성 로그가 폭증하는지 확인한 뒤, cp /dev/null /var/log/...log 명령어로 서비스 중단 없이 용량이 큰 로그 파일의 공간을 즉시 확보합니다. (원본 파일을 무작정 rm으로 지우면 프로세스가 파일 디스크립터를 쥐고 있어 디스크 공간이 반환되지 않음) 이후 오래된 아카이브 압축본(.gz)을 다른 스토리지로 수동 이관하거나 즉시 삭제합니다.

장기 대응 (아키텍처 개선): 본 프로젝트에서 구현한 보너스 2 로그 보존 정책(Log Rotation) 및 최대 용량 제한 로직(10MB/10개)을 명확히 시스템에 정착시킵니다. 궁극적으로는 로컬 디스크에 로그를 적재하지 않고 Fluentd나 Logstash 같은 수집기를 링크하여 외부의 중앙 집중형 로그 저장소(Elasticsearch, 클라우드 오브젝트 스토리지)로 실시간 포워딩하도록 인프라 파이프라인을 고도화해야 합니다.