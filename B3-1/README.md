# B3-1 내가 만든 웹사이트를 인터넷에 올리기

AWS 서울 리전(`ap-northeast-2`)에 VPC, Public Subnet, Internet Gateway, Route Table, Security Group, EC2/Nginx를 CloudFormation으로 배포한다.

## 구현 범위

- VPC `10.0.0.0/16` 안에 Public Subnet `10.0.1.0/24` 1개 구성
- `0.0.0.0/0 → Internet Gateway` 기본 경로 구성
- `t3.micro` EC2 1대와 8 GiB gp3 EBS 구성
- HTTP 80은 전체 공개, SSH 22는 배포 인자로 받은 개인 CIDR만 허용
- UserData로 Nginx와 `/health` 엔드포인트 설치
- 기존 B1-1 포트폴리오를 `publish-site.sh`로 Nginx에 업로드 가능
- 전용 IAM 정책에서 EC2/VPC/CloudFormation 작업과 SSM AMI 조회만 허용하고 `AdministratorAccess`는 사용하지 않음

## 배포

사전 조건: AWS CLI 로그인, 서울 리전 권한, EC2 키페어, 개인키 권한 `400` 또는 `600`.

루트 계정 대신 별도 IAM 사용자 또는 Role에 [`iam/deployment-policy.json`](iam/deployment-policy.json)을 부착해 배포한다. 이 정책은 서울 리전의 CloudFormation 스택과 EC2/VPC/SSM 작업만 허용하며 `AdministratorAccess`를 부여하지 않는다.

```bash
cd B3-1
chmod +x scripts/*.sh
./scripts/deploy.sh codyssey-b3-1 <KEY_PAIR_NAME> <MY_PUBLIC_IP>/32 <PRIVATE_KEY.pem>
```

기존에 만든 포트폴리오를 배포하려면:

```bash
./scripts/publish-site.sh \
  codyssey-b3-1 \
  <PRIVATE_KEY.pem> \
  "../B1-1 나를 소개하는 웹페이지 처음부터 만들기"
```

## 인스턴스 중지·재시작

최종 삭제 전에는 인스턴스만 중지했다가 다시 시작할 수 있다. 중지하면 EC2 컴퓨팅 비용은 멈추지만 EBS 비용은 남으며, 재시작 후 퍼블릭 IP가 바뀔 수 있다.

```bash
AWS_PROFILE=codyssey-b31 ./scripts/instance-power.sh codyssey-b3-1 stop
AWS_PROFILE=codyssey-b31 ./scripts/instance-power.sh codyssey-b3-1 start
AWS_PROFILE=codyssey-b31 ./scripts/instance-power.sh codyssey-b3-1 status
```

`destroy.sh`는 VPC와 EC2를 완전히 삭제하므로 이후에는 `start`로 다시 켤 수 없다. 다시 생성하려면 `deploy.sh`를 실행한다.

## 외부 접속 검증 방식: A

배포 후 브라우저에서 `http://<PUBLIC_IP>/`를 열어 포트폴리오 페이지가 정상 표시되는지 확인한다. `/health`의 `200 OK` 응답도 보조 검증으로 확인한다.

```bash
./scripts/verify.sh codyssey-b3-1
```

실제 배포 결과:

- 선택 방식: A
- URL: `http://54.180.128.61/`
- Public IP: `54.180.128.61`
- 검증 일시: `2026-09-23 17:22 KST`
- 응답: 포트폴리오 페이지 정상 표시
- 보조 검증: `GET /health` → `200 OK`, 본문 `OK`
- 페이지 스크린샷: [`proof/site.png`](proof/site.png)
- Health 스크린샷: [`proof/health.png`](proof/health.png)

## 제출 파일

- 아키텍처: [`docs/architecture.png`](docs/architecture.png)
- 트러블슈팅: [`docs/troubleshooting.md`](docs/troubleshooting.md)
- 정리 체크리스트: [`docs/cleanup-checklist.md`](docs/cleanup-checklist.md)
- CloudFormation 스택: [`proof/cloudformation-stack.png`](proof/cloudformation-stack.png)
- CloudFormation 리소스: [`proof/cloudformation-resources.png`](proof/cloudformation-resources.png)
- EC2 실행 상태: [`proof/ec2-running-list.png`](proof/ec2-running-list.png), [`proof/ec2-running.png`](proof/ec2-running.png)
- 라우팅 테이블: [`proof/route-table.png`](proof/route-table.png)
- 보안 그룹: [`proof/security-group.png`](proof/security-group.png)
- 삭제 증빙: [`proof/cleanup.png`](proof/cleanup.png)
- 인프라 코드: [`infra/template.yaml`](infra/template.yaml)
- 최소권한 정책: [`iam/deployment-policy.json`](iam/deployment-policy.json)

## 정리

실습이 끝나면 반드시 삭제한다.

```bash
./scripts/destroy.sh codyssey-b3-1
```

삭제 후 [`docs/cleanup-checklist.md`](docs/cleanup-checklist.md)의 EC2, EBS, Elastic IP, Internet Gateway, VPC, Billing 항목을 실제 상태로 체크한다.

실제 AWS 계정에서 배포하지 않은 상태에서는 Public IP, 접속 스크린샷, 삭제 완료를 성공으로 기재하지 않는다.
