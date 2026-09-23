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

## 외부 접속 검증 방식: B

배포 후 다음 명령으로 `GET http://<PUBLIC_IP>/health`의 `200 OK`와 본문 `OK`를 확인한다.

```bash
./scripts/verify.sh codyssey-b3-1
```

실제 배포 뒤 아래 값을 채우고 결과 화면을 `proof/health.png`로 저장한다.

- 선택 방식: B
- URL: `http://54.180.141.122/health`
- Public IP: `54.180.141.122`
- 검증 일시: `2026-09-23 16:27 KST`
- 응답: `200 OK`, 본문 `OK`
- 스크린샷: `proof/health.png`

## 제출 파일

- 아키텍처: [`docs/architecture.png`](docs/architecture.png)
- 트러블슈팅: [`docs/troubleshooting.md`](docs/troubleshooting.md)
- 정리 체크리스트: [`docs/cleanup-checklist.md`](docs/cleanup-checklist.md)
- 인프라 코드: [`infra/template.yaml`](infra/template.yaml)
- 최소권한 정책: [`iam/deployment-policy.json`](iam/deployment-policy.json)

## 정리

실습이 끝나면 반드시 삭제한다.

```bash
./scripts/destroy.sh codyssey-b3-1
```

삭제 후 [`docs/cleanup-checklist.md`](docs/cleanup-checklist.md)의 EC2, EBS, Elastic IP, Internet Gateway, VPC, Billing 항목을 실제 상태로 체크한다.

실제 AWS 계정에서 배포하지 않은 상태에서는 Public IP, 접속 스크린샷, 삭제 완료를 성공으로 기재하지 않는다.
