#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "사용법: $0 <STACK_NAME> <start|stop|status>" >&2
    exit 2
}

[[ $# -eq 2 ]] || usage
STACK_NAME=$1
ACTION=$2
REGION=${AWS_REGION:-ap-northeast-2}

case "$ACTION" in
    start|stop|status) ;;
    *) usage ;;
esac

INSTANCE_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
    --output text)

if [[ "$ACTION" == status ]]; then
    aws ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --region "$REGION" \
        --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress]' \
        --output table
    exit 0
fi

if [[ "$ACTION" == start ]]; then
    aws ec2 start-instances --instance-ids "$INSTANCE_ID" --region "$REGION" >/dev/null
    aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"
else
    aws ec2 stop-instances --instance-ids "$INSTANCE_ID" --region "$REGION" >/dev/null
    aws ec2 wait instance-stopped --instance-ids "$INSTANCE_ID" --region "$REGION"
fi

aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION" \
    --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress]' \
    --output table
