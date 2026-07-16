#!/bin/bash

# 1. 환경 변수 강제 로드 (cron 환경 대비)
source /home/agent-admin/.bashrc

LOG_FILE="/var/log/agent-app/monitor.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# 2. Health Check (실패 시 즉시 exit 1 종료)
# 프로세스 명칭 'agent_app' 추적
PID=$(pgrep -f "agent_app")
if [ -z "$PID" ]; then
    echo "[$TIMESTAMP] [CRITICAL] agent_app process not found." >> $LOG_FILE
    exit 1
fi

# 포트 15034 LISTEN 상태 확인
PORT_CHECK=$(ss -tuln | grep ":15034")
if [ -z "$PORT_CHECK" ]; then
    echo "[$TIMESTAMP] [CRITICAL] Port 15034 is not listening." >> $LOG_FILE
    exit 1
fi

# 3. 상태 점검 (방화벽 활성화 여부 확인 - 비활성 시 WARNING만 출력)
UFW_STATUS=$(sudo ufw status | grep "Status: active")
if [ -z "$UFW_STATUS" ]; then
    echo "[$TIMESTAMP] [WARNING] Firewall (UFW) is inactive." >> $LOG_FILE
fi

# 4. 자원 수集 (CPU, MEM, DISK)
# top 명령어 기준 순간 CPU 사용률 (100 - idle)
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8}')
# free 명령어 기준 메모리 사용률 (%)
MEM_USAGE=$(free | grep Mem | awk '{print $3/$2 * 100.0}')
# 디스크 루트 파티션 사용률 (%)
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')

# 소수점 출력을 깔끔하게 다듬기
CPU_INT=$(printf "%.0f" "$CPU_USAGE")
MEM_INT=$(printf "%.0f" "$MEM_USAGE")

# 5. 표준 로그 포맷에 맞춰 기록
LOG_MSG="[$TIMESTAMP] PID:$PID CPU:${CPU_INT}% MEM:${MEM_INT}% DISK_USED:${DISK_USAGE}%"
echo "$LOG_MSG" >> $LOG_FILE

# 6. 임계값 경고 판단 (경고 로그 누적)
if [ "$CPU_INT" -gt 20 ]; then
    echo "[$TIMESTAMP] [WARNING] CPU threshold exceeded! (Current: ${CPU_INT}%)" >> $LOG_FILE
fi

if [ "$MEM_INT" -gt 10 ]; then
    echo "[$TIMESTAMP] [WARNING] MEM threshold exceeded! (Current: ${MEM_INT}%)" >> $LOG_FILE
fi

if [ "$DISK_USAGE" -gt 80 ]; then
    echo "[$TIMESTAMP] [WARNING] DISK threshold exceeded! (Current: ${DISK_USAGE}%)" >> $LOG_FILE
fi