# B3-1 트러블슈팅 보고서

> 아래 기록은 배포 후 실제 값으로 채우는 문서다. 실행하지 않은 AWS 결과를 성공으로 적지 않는다.

## 사례: CloudFormation이 Internet Gateway 연결 단계에서 롤백됨

| 단계 | 기록 |
| --- | --- |
| 증상 | 첫 번째 `codyssey-b3-1` Stack이 `ROLLBACK_COMPLETE`로 종료됐다. |
| 원인 가설 | 템플릿 오류 또는 배포 IAM 사용자 권한 누락을 의심했다. |
| 검증 | CloudFormation 이벤트에서 `InternetGatewayAttachment`의 `ec2:AttachInternetGateway` 권한 거부를 확인했다. |
| 조치 | IAM 정책에 `ec2:AttachInternetGateway`를 추가하고 실패 Stack을 삭제한 뒤 재배포했다. 진단용 `cloudformation:DescribeEvents`도 추가했다. |
| 결과 | `2026-09-23` 재배포 성공. Public IP `54.180.141.122`, `/health` 응답 `200 OK`와 `OK` 확인. |
| 재발 방지 | 정책 파일을 배포 전에 검증하고, 배포 후 `verify.sh`를 실행한다. VPC 연결 권한을 정책에 유지한다. |

### 실제 검증 기록

- 실행 일시: `2026-09-23 16:27 KST`
- 스택: `codyssey-b3-1`
- Public IP: `54.180.141.122`
- 명령: `./scripts/verify.sh codyssey-b3-1`
- 결과: `EC2 status: ok`, `GET /health → OK`, 외부 접속 검증 성공
- 증빙: `../proof/health.png`
