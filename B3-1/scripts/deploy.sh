#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "사용법: $0 <stack-name> <key-pair-name> <ssh-cidr> <private-key-path>" >&2
    echo "예시: $0 codyssey-b3-1 my-key 198.51.100.10/32 ~/.ssh/my-key.pem" >&2
    exit 2
}

[[ $# -eq 4 ]] || usage

STACK_NAME=$1
KEY_NAME=$2
SSH_CIDR=$3
KEY_FILE=$4
REGION=${AWS_REGION:-ap-northeast-2}
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TEMPLATE="$SCRIPT_DIR/../infra/template.yaml"

[[ -f "$KEY_FILE" ]] || { echo "키 파일이 없습니다: $KEY_FILE" >&2; exit 1; }
[[ "$SSH_CIDR" != "0.0.0.0/0" ]] || { echo "SSH를 0.0.0.0/0으로 열 수 없습니다." >&2; exit 1; }
[[ "$SSH_CIDR" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}/([0-9]|[12][0-9]|3[0-2])$ ]] || {
    echo "SSH CIDR 형식이 잘못되었습니다: $SSH_CIDR" >&2
    exit 1
}
IFS=./ read -r octet_1 octet_2 octet_3 octet_4 prefix <<< "$SSH_CIDR"
for octet in "$octet_1" "$octet_2" "$octet_3" "$octet_4"; do
    ((octet <= 255)) || { echo "SSH CIDR의 IP 옥텟이 잘못되었습니다: $SSH_CIDR" >&2; exit 1; }
done
((prefix >= 16)) || { echo "SSH CIDR은 /16보다 넓을 수 없습니다: $SSH_CIDR" >&2; exit 1; }

command -v aws >/dev/null || { echo "aws CLI가 필요합니다." >&2; exit 1; }
key_mode=$(stat -c '%a' "$KEY_FILE")
case "$key_mode" in
    400|600) ;;
    *) echo "개인 키 권한은 400 또는 600이어야 합니다. 현재: $key_mode" >&2; exit 1 ;;
esac

aws sts get-caller-identity --region "$REGION" >/dev/null
AMI_ID=$(aws ssm get-parameter \
    --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
    --query 'Parameter.Value' --output text --region "$REGION")

aws cloudformation deploy \
    --template-file "$TEMPLATE" \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --no-fail-on-empty-changeset \
    --parameter-overrides \
        "AmiId=$AMI_ID" \
        "KeyName=$KEY_NAME" \
        "AllowedSshCidr=$SSH_CIDR"

INSTANCE_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' --output text)
PUBLIC_IP=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`PublicIp`].OutputValue' --output text)

aws ec2 wait instance-status-ok --instance-ids "$INSTANCE_ID" --region "$REGION"
printf '배포 완료\nPublic IP: %s\nHealth URL: http://%s/health\n' "$PUBLIC_IP" "$PUBLIC_IP"
