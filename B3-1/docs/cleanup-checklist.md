# 리소스 정리 체크리스트

정리 명령:

```bash
./scripts/destroy.sh <STACK_NAME>
```

- [x] EC2 인스턴스가 `terminated` 상태인지 확인
- [x] CloudFormation 스택 삭제 완료 확인
- [x] EBS 볼륨에 `available` 잔여 항목이 없는지 확인
- [x] Elastic IP를 생성하지 않음 (`template.yaml`에 EIP 리소스 없음)
- [x] Internet Gateway가 VPC에서 분리되고 삭제되었는지 확인
- [x] VPC, Public Subnet, Route Table, Security Group 삭제 확인
- [x] NAT Gateway/ELB/ALB/RDS를 생성하지 않음
- [ ] Billing Dashboard에서 예상하지 않은 과금 리소스가 없는지 확인할 것 (계정 소유자 확인 필요)

확인 명령 예시:

```bash
aws cloudformation describe-stack-resources --stack-name <STACK_NAME> \
  --query 'StackResources[].[LogicalResourceId,ResourceType,ResourceStatus]' --output table
aws ec2 describe-addresses --query 'Addresses[?AssociationId!=null].[PublicIp,AllocationId]' --output table
```

## 실제 정리 결과

- 정리 일시: `2026-09-23 17:31 KST`
- `destroy.sh` 출력: `스택 삭제 완료`
- CloudFormation: `codyssey-b3-1`을 찾을 수 없음
- EC2: 실행 중인 인스턴스 없음
- EBS: 전체 볼륨 없음
- VPC: `vpc-0c9f3f8e8c1ec5010`을 찾을 수 없음
- Internet Gateway: `igw-0f709d2069b659b26`를 찾을 수 없음
- Elastic IP: 템플릿에서 생성하지 않음
- 삭제 증빙: `../proof/cleanup.png`
