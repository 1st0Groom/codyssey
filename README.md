# 코디세이(Codyssey) 개발 워크스테이션 구축 프로젝트

## 1. 프로젝트 개요
- **목적:** 로컬 개발 환경 세팅, 재현 가능한 실행 환경 공유, 협업 기반 소스코드 관리를 위한 워크스테이션 구축
- **핵심 기술:** Linux CLI, Docker, Git/GitHub

## 2. 실행 환경 (Verified)
- **Host OS:** Ubuntu 24.04.4 LTS (Kernel 6.17.0)
- **Hardware:** ROG Zephyrus G14 (camus-G14)
- **Docker:** 29.3.1 (Server Version)
- **Git:** 2.43.0
- **User:** camus (nadomolla08@naver.com)
- **Workdir:** /home/camus/workspace/codyssey

## 3. 수행 항목 체크리스트
- [x] 터미널 기본 조작 및 작업 디렉토리 구성
- [x] 권한 변경 실습 (chmod 755/644)
- [x] Git 설정 및 로컬 리포지토리 초기화
- [x] Docker 설치 및 사용자 그룹 권한 설정
- [x] hello-world 및 ubuntu 컨테이너 실행/진입 실습
- [x] 커스텀 Dockerfile 작성, 빌드 및 실행
- [x] 포트 매핑(8080, 8090)을 통한 호스트-컨테이너 통신 증명
- [x] 바인드 마운트(Bind Mount)를 이용한 실시간 소스 동기화 검증
- [x] 도커 볼륨(Volume)을 활용한 데이터 영속성 검증
- [x] GitHub 원격 저장소 연동 및 최종 산출물 Push 완료

## 4. 검증 방법 및 수행 로그

### 4.1. 터미널 조작 및 권한 변경 실습
```bash
$mkdir -p ~/workspace/codyssey/src$ touch src/index.html
$chmod 755 src/index.html$ ls -l src/index.html
-rwxr-xr-x 1 camus camus 50 Mar 31 17:42 src/index.html
$chmod 644 src/index.html$ ls -l src/index.html
-rw-r--r-- 1 camus camus 50 Mar 31 17:42 src/index.html
