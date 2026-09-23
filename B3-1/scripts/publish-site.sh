#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "사용법: $0 <stack-name> <private-key-path> <site-directory>" >&2
    exit 2
}

[[ $# -eq 3 ]] || usage
STACK_NAME=$1
KEY_FILE=$2
SITE_DIR=$3
REGION=${AWS_REGION:-ap-northeast-2}

command -v aws >/dev/null || { echo "aws CLI가 필요합니다." >&2; exit 1; }
command -v ssh >/dev/null || { echo "ssh가 필요합니다." >&2; exit 1; }
command -v tar >/dev/null || { echo "tar가 필요합니다." >&2; exit 1; }
[[ -f "$KEY_FILE" ]] || { echo "키 파일이 없습니다: $KEY_FILE" >&2; exit 1; }
[[ -d "$SITE_DIR" ]] || { echo "웹사이트 폴더가 없습니다: $SITE_DIR" >&2; exit 1; }

PUBLIC_IP=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`PublicIp`].OutputValue' --output text)

SSH_OPTS=(
    -i "$KEY_FILE"
    -o ConnectTimeout=5
    -o StrictHostKeyChecking=accept-new
)

ready=false
for _ in $(seq 1 60); do
    if ssh "${SSH_OPTS[@]}" "ec2-user@$PUBLIC_IP" true >/dev/null 2>&1; then
        ready=true
        break
    fi
    sleep 5
done
[[ "$ready" == true ]] || { echo "SSH 접속 준비 시간 초과: $PUBLIC_IP" >&2; exit 1; }

# tar 스트림으로 기존 포트폴리오 정적 파일을 EC2의 nginx 문서 루트에 배포한다.
tar -C "$SITE_DIR" -czf - . | ssh "${SSH_OPTS[@]}" "ec2-user@$PUBLIC_IP" \
    'sudo find /var/www/site -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + && sudo tar -xzf - -C /var/www/site && sudo nginx -t && sudo systemctl reload nginx'

printf '사이트 배포 완료: http://%s/\n' "$PUBLIC_IP"
