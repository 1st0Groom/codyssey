# 리소스 정리 체크리스트

정리 명령:

```bash
./scripts/destroy.sh <STACK_NAME>
```

- [ ] EC2 인스턴스가 `terminated` 상태인지 확인
- [ ] CloudFormation 스택 삭제 완료 확인
- [ ] EBS 볼륨에 `available` 잔여 항목이 없는지 확인
- [ ] Elastic IP를 생성했다면 `Release` 완료 확인
- [ ] Internet Gateway가 VPC에서 분리되고 삭제되었는지 확인
- [ ] VPC, Public Subnet, Route Table, Security Group 삭제 확인
- [ ] NAT Gateway/ELB/ALB/RDS를 생성했다면 삭제 확인
- [ ] Billing Dashboard에 예상하지 않은 과금 리소스가 없는지 확인

확인 명령 예시:

```bash
aws cloudformation describe-stack-resources --stack-name <STACK_NAME> \
  --query 'StackResources[].[LogicalResourceId,ResourceType,ResourceStatus]' --output table
aws ec2 describe-addresses --query 'Addresses[?AssociationId!=null].[PublicIp,AllocationId]' --output table
```

실제 정리 일시: `TODO: YYYY-MM-DD HH:MM KST`
