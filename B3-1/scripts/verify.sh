#!/usr/bin/env bash
set -euo pipefail

[[ $# -eq 1 ]] || { echo "사용법: $0 <stack-name>" >&2; exit 2; }
STACK_NAME=$1
REGION=${AWS_REGION:-ap-northeast-2}

PUBLIC_IP=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`PublicIp`].OutputValue' --output text)
INSTANCE_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' --output text)

aws ec2 describe-instance-status --instance-ids "$INSTANCE_ID" --region "$REGION" \
    --query 'InstanceStatuses[0].InstanceStatus.Status' --output text
printf 'GET http://%s/health\n' "$PUBLIC_IP"
curl --fail --silent --show-error --max-time 10 "http://$PUBLIC_IP/health"
printf '\n외부 접속 검증 성공\n'
