# B3-1 AWS 개념과 생성 흐름

이 문서는 현재 B3-1 구현을 읽기 위한 학습 자료다. 목표는 `CloudFormation`으로 만든 단일 EC2 웹 서버를 서울 리전에 배포하고, 기존 B1-1 웹사이트를 인터넷에 공개하는 것이다.

관련 파일:

- 인프라 정의: [`../infra/template.yaml`](../infra/template.yaml)
- 권한 정책: [`../iam/deployment-policy.json`](../iam/deployment-policy.json)
- 배포 명령: [`../scripts/deploy.sh`](../scripts/deploy.sh)
- 사이트 업로드: [`../scripts/publish-site.sh`](../scripts/publish-site.sh)
- 외부 접속 확인: [`../scripts/verify.sh`](../scripts/verify.sh)

## 1. 먼저 결론

현재 구성은 다음과 같다.

```text
인터넷
  │ HTTP :80
  ▼
공인 IPv4를 가진 EC2 / Nginx
  │
Public Subnet 10.0.1.0/24
  │ Route Table: 0.0.0.0/0 → Internet Gateway
  ▼
VPC 10.0.0.0/16
```

현재는 미션을 최소한으로 수행하기 위한 구조다.

- 리전 1개: 서울 `ap-northeast-2`
- 가용 영역 1개
- 서브넷 1개
- EC2 1대
- EBS 디스크 1개
- HTTP만 공개
- SSH는 현재 내 공인 IP만 허용

따라서 현재 구성은 **이중화되지 않았다**. 서버나 가용 영역에 문제가 생기면 서비스가 중단될 수 있다. 미션의 요구사항은 웹사이트를 인터넷에 올리는 것이므로, 이중화는 비용과 복잡도를 늘리는 선택 사항이다.

## 2. AWS 계정과 로그인 개념

### Root user

AWS 계정을 처음 만든 주인 계정이다. 결제, 계정 복구, IAM 최초 설정처럼 계정 전체에 영향을 주는 작업에 사용한다.

일상적인 CLI 작업에는 Root user의 Access Key를 사용하지 않는다. Root Access Key가 유출되면 계정 전체가 위험해진다.

### IAM user

AWS 안에서 작업할 사람 또는 프로그램을 나타내는 사용자다. B3-1에서는 `codyssey-b31-deployer`라는 전용 사용자를 만들고, 필요한 권한만 부여한다.

### Access Key

AWS CLI가 API를 호출할 때 사용하는 자격 증명이다.

- Access Key ID: 사용자 이름과 비슷한 공개 식별자
- Secret Access Key: 비밀번호와 비슷한 비밀 값
- 둘 다 Git, 마크다운, 채팅에 올리지 않는다.
- 과제가 끝나면 Access Key를 비활성화하거나 삭제한다.

### AWS CLI profile

`aws configure --profile codyssey-b31`로 저장한 로그인 설정 이름이다. 다음 명령으로 현재 터미널이 사용할 프로필을 선택한다.

```bash
export AWS_PROFILE=codyssey-b31
```

프로필은 AWS 리전이 아니다. 프로필은 “누구로 로그인할지”, 리전은 “어느 AWS 지역에서 작업할지”를 뜻한다.

### Region과 Availability Zone

- Region: 서울, 도쿄, 버지니아처럼 지리적으로 분리된 AWS 지역
- Availability Zone, AZ: 하나의 Region 안에서 분리된 데이터센터 그룹
- 현재 Region: 서울 `ap-northeast-2`
- 현재 템플릿: 서울의 첫 번째 AZ에 서브넷 하나 생성

Region은 큰 지역이고 AZ는 그 안의 독립된 장애 영역이다. 같은 Region 안의 여러 AZ를 사용하면 한 AZ 장애에 대비할 수 있다.

## 3. IAM 정책 읽는 법

IAM 정책은 “누가 AWS에서 무엇을 할 수 있는가”를 JSON으로 적은 문서다. 정책을 IAM 사용자, 그룹, Role에 붙이면 해당 권한이 적용된다.

현재 정책의 기본 형태는 다음과 같다.

```json
{
  "Effect": "Allow",
  "Action": ["ec2:RunInstances"],
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "aws:RequestedRegion": "ap-northeast-2"
    }
  }
}
```

| 항목 | 뜻 |
|---|---|
| `Effect` | `Allow` 또는 `Deny` |
| `Action` | 허용하거나 거부할 API 작업 |
| `Resource` | 작업 대상 AWS 리소스 |
| `Condition` | 특정 조건에서만 허용 |
| `aws:RequestedRegion` | 서울 리전에서 요청한 작업만 허용 |

### B3-1 정책이 허용하는 작업

| 정책 묶음 | 하는 일 |
|---|---|
| `ec2:*` 일부 | VPC, 서브넷, 라우팅, 보안 그룹, EC2, EBS 생성·조회·삭제 |
| `ec2:DescribeInstanceStatus` | EC2가 실제로 준비됐는지 확인 |
| `ssm:GetParameter` | 서울 리전의 최신 Amazon Linux 2023 AMI ID 조회 |
| `cloudformation:*` 일부 | 스택 생성, 변경, 조회, 삭제 |

이 정책에는 IAM 사용자 생성 권한이나 `AdministratorAccess`가 없다. 그래서 Root user가 먼저 정책과 배포용 IAM 사용자를 만든다.

### 최소 권한

최소 권한은 작업에 필요한 권한만 주는 원칙이다. B3-1에서는 다음처럼 범위를 줄였다.

- 서울 리전만 허용
- EC2/VPC/CloudFormation 작업만 허용
- IAM 자체를 수정하는 권한은 제외
- SSH는 내 현재 IP만 허용

`Resource: "*"`는 모든 리소스를 무조건 공개한다는 뜻과는 다르다. EC2 생성·조회처럼 리소스 ARN을 세밀하게 지정하기 어려운 API가 있어 이 예제에서는 사용한다. 대신 리전 조건과 Action 목록으로 범위를 제한한다.

## 4. CloudFormation 개념

### Template

[`template.yaml`](../infra/template.yaml)은 원하는 AWS 상태를 선언한 설계도다.

```yaml
Resources:
  WebServer:
    Type: AWS::EC2::Instance
```

이렇게 작성하면 “EC2를 하나 만들고 싶다”고 선언한다. 직접 콘솔에서 여러 번 클릭하는 대신 파일에 인프라를 기록한다.

### Stack

Template을 바탕으로 실제 AWS 리소스를 묶어 관리하는 단위다. B3-1의 스택 이름은 `codyssey-b3-1`이다.

- Stack 생성: 템플릿의 리소스 생성
- Stack 업데이트: 템플릿 변경분 적용
- Stack 삭제: 스택이 만든 리소스 일괄 삭제

그래서 B3-1은 EC2만 따로 지우지 않고 마지막에 Stack 전체를 삭제한다.

### Parameters

배포 시 외부에서 입력받는 값이다.

| Parameter | 값 |
|---|---|
| `AmiId` | Amazon Linux 2023 이미지 ID |
| `KeyName` | EC2에 연결할 키페어 이름 |
| `AllowedSshCidr` | SSH를 허용할 IP 범위 |

### Resources

실제로 만들어지는 AWS 리소스다.

```text
VPC
 ├─ Internet Gateway
 ├─ Public Subnet
 ├─ Route Table + Route
 ├─ Security Group
 └─ EC2 + EBS
```

### Outputs

스택 생성 후 밖으로 보여줄 값이다. 현재는 `InstanceId`와 `PublicIp`만 출력한다.

### UserData

EC2가 처음 시작될 때 한 번 실행되는 초기 설정 스크립트다. 현재 UserData는 다음을 한다.

1. Nginx 설치
2. `/var/www/site` 생성
3. 기본 HTML 생성
4. `/health`가 `OK`를 반환하도록 Nginx 설정
5. Nginx 시작 및 부팅 시 자동 시작 설정

### CloudFormation과 Terraform의 관계

둘 다 IaC, 즉 Infrastructure as Code 도구다.

| 항목 | CloudFormation | Terraform |
|---|---|---|
| 관리 주체 | AWS | HashiCorp와 Provider |
| 설정 파일 | YAML/JSON | HCL |
| 관리 단위 | Stack | Terraform state와 리소스 |
| B3-1 사용 여부 | 사용 | 사용하지 않음 |

둘 다 인프라를 코드로 재현한다는 점은 비슷하지만 명령어와 상태 관리 방식은 다르다. 현재 미션은 CloudFormation 템플릿으로 구현되어 있다.

## 5. 네트워크 개념

### VPC

VPC는 AWS 안에 만드는 논리적인 사설 네트워크다. B3-1은 다음 주소 공간을 사용한다.

```text
VPC:           10.0.0.0/16
Public Subnet: 10.0.1.0/24
```

`/16`과 `/24`는 CIDR 표기다. 앞부분이 네트워크 범위를 나타내고, 뒤 숫자가 작을수록 더 넓은 주소 범위다.

- `10.0.0.0/16`: VPC 전체 주소 범위
- `10.0.1.0/24`: 그 안에서 EC2를 넣을 작은 네트워크 구역
- 서브넷 주소는 VPC 주소 범위 안에 들어가야 한다.

### Subnet

서브넷은 VPC를 잘게 나눈 네트워크 구역이다. 하나의 서브넷은 하나의 AZ 안에만 존재한다.

현재 서브넷은 `MapPublicIpOnLaunch: true`라서 EC2 시작 시 공인 IPv4를 받을 수 있다.

### Internet Gateway

VPC와 인터넷 사이를 연결하는 출입구다. 단, Internet Gateway만 붙인다고 인터넷이 되는 것은 아니다. Route Table에 인터넷으로 가는 경로가 있어야 한다.

### Route Table

네트워크 패킷을 어디로 보낼지 정하는 길 안내표다.

현재 핵심 규칙은 다음과 같다.

```text
목적지 0.0.0.0/0 → Internet Gateway
```

`0.0.0.0/0`은 “특정하지 않은 모든 IPv4 목적지”라는 뜻이다. 이 경로와 공인 IP가 있어 EC2가 인터넷과 통신할 수 있다.

### Public Subnet과 Private Subnet

- Public Subnet: Internet Gateway로 가는 기본 경로가 있는 서브넷
- Private Subnet: 인터넷에서 직접 들어오는 경로가 없는 서브넷

현재 EC2는 패키지를 설치해야 하므로 Public Subnet에 둔다. 운영 환경에서는 웹 진입점만 Public으로 두고 애플리케이션 서버를 Private으로 두는 구성이 흔하다.

### Security Group

Security Group은 EC2 네트워크 인터페이스에 붙는 가상 방화벽이다.

현재 규칙:

| 방향 | 포트 | 출발지/목적지 | 이유 |
|---|---:|---|---|
| Inbound | 80 | `0.0.0.0/0` | 누구나 웹사이트 접속 |
| Inbound | 22 | 내 공인 IP `/32` | SSH 관리 |
| Outbound | 전체 | `0.0.0.0/0` | Nginx 패키지 설치와 응답 |

`/32`는 IP 하나만 뜻한다. 예를 들어 `203.0.113.10/32`는 그 IP 하나에서만 SSH를 허용한다.

집이나 카페의 공인 IP가 바뀌면 SSH가 막힐 수 있다. 그때는 새 IP를 넣어 Stack을 업데이트해야 한다. SSH를 `0.0.0.0/0`으로 여는 것은 피한다.

### 포트

- 22: SSH 원격 터미널
- 80: HTTP 웹 요청
- 443: HTTPS 웹 요청. 현재 미션 구성에는 아직 없음

현재는 IP 주소로 `http://PUBLIC_IP/`에 접속한다. 도메인, HTTPS 인증서, 로드밸런서는 요구사항이 아니므로 넣지 않았다.

## 6. EC2와 웹사이트 배포 개념

### AMI

AMI는 EC2를 시작할 때 사용하는 운영체제 이미지다. 배포 스크립트는 SSM Public Parameter에서 서울 리전의 최신 Amazon Linux 2023 AMI ID를 조회한다.

### EC2

EC2는 AWS에서 빌리는 가상 서버다. 현재 타입은 `t3.micro` 한 대다.

### EBS

EBS는 EC2에 연결되는 디스크다. 현재는 `gp3`, 8 GiB이며 EC2가 삭제될 때 같이 삭제되도록 설정했다.

### EC2 키페어와 SSH

키페어는 공개키와 개인키 한 쌍이다.

```text
AWS EC2: 공개키 저장
내 컴퓨터: 개인키 .pem 보관
```

SSH 접속 시 AWS에 저장된 공개키와 내 컴퓨터의 개인키가 짝이 맞는지 확인한다. 개인키를 웹사이트 폴더나 Git 저장소에 넣지 않는다.

### Nginx

Nginx는 EC2에서 HTTP 요청을 받아 파일을 반환하는 웹 서버다.

- `/`: `/var/www/site`의 웹사이트 파일
- `/health`: 서버가 살아 있는지 확인하는 간단한 검사 주소

`publish-site.sh`는 기존 B1-1 파일을 tar 스트림으로 EC2에 보내 `/var/www/site`에 배치한 뒤 Nginx를 reload한다.

## 7. 실제 생성 흐름

### 전체 흐름

```text
AWS Root 로그인
   ↓
IAM 정책 생성
   ↓
배포용 IAM 사용자 + Access Key 생성
   ↓
AWS CLI profile 설정
   ↓
EC2 키페어 생성
   ↓
deploy.sh 실행
   ↓
SSM에서 AMI ID 조회
   ↓
CloudFormation Stack 생성
   ↓
VPC → IGW → Subnet → Route Table → Security Group
   ↓
EC2 + EBS 생성
   ↓
UserData로 Nginx 설치
   ↓
publish-site.sh로 B1-1 사이트 업로드
   ↓
verify.sh로 /health 외부 접속 확인
   ↓
스크린샷 저장
   ↓
destroy.sh로 Stack 삭제
```

### 배포 스크립트 내부 흐름

```text
./scripts/deploy.sh
  ├─ 인자 확인: 스택명, 키페어명, SSH CIDR, .pem 경로
  ├─ 현재 IP가 0.0.0.0/0인지 검사
  ├─ 개인키 권한이 400 또는 600인지 검사
  ├─ aws sts get-caller-identity로 로그인 확인
  ├─ SSM에서 Amazon Linux 2023 AMI ID 조회
  ├─ cloudformation deploy로 템플릿 적용
  ├─ Stack Output에서 InstanceId/PublicIp 조회
  ├─ EC2 상태가 준비될 때까지 대기
  └─ Public IP와 Health URL 출력
```

### 실행 명령

```bash
cd /home/camus/workspace/codyssey/B3-1
export AWS_PROFILE=codyssey-b31

MY_IP=$(curl -4 -s https://checkip.amazonaws.com | tr -d '\n')

./scripts/deploy.sh \
  codyssey-b3-1 \
  codyssey-b31-key \
  "${MY_IP}/32" \
  ~/.ssh/codyssey-b31-key.pem
```

배포 후 사이트를 올린다.

```bash
./scripts/publish-site.sh \
  codyssey-b3-1 \
  ~/.ssh/codyssey-b31-key.pem \
  "../B1-1 나를 소개하는 웹페이지 처음부터 만들기"
```

외부 접속을 확인한다.

```bash
./scripts/verify.sh codyssey-b3-1
```

## 8. 이중화 개념

### 이중화, 고가용성, 확장성, 백업은 다르다

| 개념 | 뜻 |
|---|---|
| 이중화 | 같은 역할을 하는 구성 요소를 둘 이상 준비 |
| 고가용성 | 장애가 나도 서비스를 계속 제공하도록 설계 |
| 확장성 | 사용자가 늘 때 처리 능력을 키울 수 있는 성질 |
| 백업 | 장애 후 데이터를 복구하기 위한 복사본 |

서버를 두 대 만든다고 자동으로 고가용성이 되는 것은 아니다. 두 서버로 트래픽을 나누고, 한 대가 죽었을 때 다른 서버로 연결되며, 데이터도 보호되어야 한다.

### 현재 구성의 장애 지점

```text
단일 Region
 └─ 단일 AZ
     └─ 단일 Subnet
         └─ 단일 EC2
             └─ 단일 EBS
```

따라서 다음은 현재 자동으로 해결되지 않는다.

- EC2 장애 시 자동 교체
- AZ 장애 시 다른 AZ로 이동
- 트래픽 증가 시 서버 수 자동 증가
- 디스크 장애 시 데이터 복구
- 도메인 기반 트래픽 분산

### 일반적인 이중화 구조

운영 서비스에서 이중화를 추가한다면 보통 다음 구조를 검토한다.

```text
인터넷
   ↓
Application Load Balancer
   ├─ Public Subnet / AZ-A
   └─ Public Subnet / AZ-B
          ↓
Auto Scaling Group
   ├─ EC2 / Private Subnet / AZ-A
   └─ EC2 / Private Subnet / AZ-B
          ↓
데이터 저장소
   ├─ Multi-AZ 데이터베이스
   └─ S3 백업
```

각 요소의 역할은 다음과 같다.

- Load Balancer: 여러 EC2로 요청 분산
- Auto Scaling Group: EC2 장애 시 새 인스턴스 생성, 필요하면 수량 조절
- 두 AZ: 한 AZ 장애 시 다른 AZ에서 서비스 유지
- Multi-AZ 데이터베이스: 데이터베이스 장애 대비
- S3 백업: 정적 파일과 백업 데이터 보관

이 구조는 더 안정적이지만 ALB, 두 개 이상의 서브넷, Auto Scaling, 추가 보안 그룹, 데이터베이스 등을 관리해야 하고 비용도 늘어난다. B3-1에서는 요구사항이 아니므로 구현하지 않았다.

## 9. 현재 구성에서 일부러 넣지 않은 것

다음은 빠뜨린 것이 아니라 미션 범위를 줄이기 위해 제외한 것이다.

| 제외 항목 | 제외 이유 |
|---|---|
| ALB | EC2 한 대라 트래픽 분산 대상이 없음 |
| Auto Scaling | 자동 복구·수평 확장이 요구되지 않음 |
| 두 번째 AZ | 이중화가 요구되지 않음 |
| NAT Gateway | EC2가 Public Subnet에서 직접 인터넷 사용 |
| RDS | 사이트가 정적 파일 기반 |
| Route 53 | 도메인 연결이 요구되지 않음 |
| ACM/HTTPS | 미션의 기본 HTTP 공개에 필요하지 않음 |
| S3 정적 호스팅 | 기존 사이트를 EC2/Nginx에 올리는 미션 흐름 사용 |
| Elastic IP | 고정 IP가 요구되지 않음 |

CloudFormation 템플릿이 커져 51,200바이트를 넘거나 Lambda 코드 같은 로컬 아티팩트를 포함하게 되면 S3 업로드 권한과 버킷 관리가 추가로 필요할 수 있다. 현재 템플릿은 작고 EC2/Nginx만 사용하므로 추가하지 않았다.

## 10. 삭제 흐름과 과금 주의

```text
destroy.sh
  ↓
CloudFormation Stack 삭제
  ↓
Stack이 만든 EC2/VPC/서브넷/보안 그룹/라우팅/EBS 삭제
  ↓
AWS 콘솔에서 잔여 리소스와 Billing 확인
```

삭제 명령:

```bash
./scripts/destroy.sh codyssey-b3-1
```

질문이 나오면 `DELETE`를 입력한다. 삭제 완료 후에도 다음을 확인한다.

- CloudFormation Stack이 없어졌는가
- EC2 인스턴스가 없어졌는가
- EBS 볼륨이 남아 있지 않은가
- Elastic IP를 따로 만들었다면 해제했는가
- Billing에 계속 발생하는 비용이 없는가
- 과제용 IAM Access Key를 비활성화하거나 삭제했는가

## 11. 핵심 용어 한 줄 정리

| 용어 | 한 줄 뜻 |
|---|---|
| Region | AWS의 지리적 지역 |
| AZ | Region 안의 분리된 장애 영역 |
| VPC | AWS 안의 논리적 사설 네트워크 |
| Subnet | VPC를 나눈 네트워크 구역 |
| Route Table | 네트워크가 갈 방향을 정하는 표 |
| Internet Gateway | VPC와 인터넷을 연결하는 출입구 |
| Security Group | EC2에 붙는 가상 방화벽 |
| EC2 | 가상 서버 |
| EBS | EC2에 붙는 디스크 |
| AMI | EC2를 시작할 운영체제 이미지 |
| IAM | AWS 권한과 사용자를 관리하는 서비스 |
| Policy | 허용할 AWS API 작업을 적은 JSON 문서 |
| CloudFormation | AWS 인프라를 코드로 생성·변경·삭제하는 서비스 |
| Stack | CloudFormation이 관리하는 리소스 묶음 |
| UserData | EC2 최초 시작 시 실행되는 초기화 스크립트 |
| Nginx | HTTP 요청을 처리하는 웹 서버 |
| Health check | 서비스가 응답하는지 확인하는 검사 |
| 이중화 | 장애 대비를 위해 같은 역할을 여러 개 준비하는 것 |

## 12. 공식 참고 자료

- [IAM 정책과 권한](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html)
- [VPC 기본 구성 요소](https://docs.aws.amazon.com/vpc/latest/userguide/how-it-works.html)
- [EC2 키페어](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/create-key-pairs.html)
- [CloudFormation 작동 방식](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-overview.html)
- [CloudFormation 템플릿](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-guide.html)
- [EC2 Auto Scaling과 여러 AZ](https://docs.aws.amazon.com/autoscaling/ec2/userguide/what-is-amazon-ec2-auto-scaling.html)
- [AWS 비용 예산](https://docs.aws.amazon.com/cost-management/latest/userguide/create-cost-budget.html)
