#!/usr/bin/env bash
set -euo pipefail

[[ $# -eq 1 ]] || { echo "사용법: $0 <stack-name>" >&2; exit 2; }
STACK_NAME=$1
REGION=${AWS_REGION:-ap-northeast-2}

read -r -p "'$STACK_NAME'의 EC2/VPC/IGW/서브넷/EBS를 삭제합니다. DELETE를 입력하세요: " answer
[[ "$answer" == DELETE ]] || { echo "취소했습니다."; exit 0; }

aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
echo "스택 삭제 완료. Elastic IP, EBS 잔여 리소스, Billing을 별도로 확인하세요."
