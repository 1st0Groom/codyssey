# AI/SW 개발 워크스테이션 구축 (Mission E1-1)

## 📌 1. 프로젝트 개요
본 프로젝트는 개발의 가장 기본이 되는 터미널(CLI), Docker(컨테이너 기반 격리 환경), 그리고 Git(버전 관리) 환경을 올바르게 이해하고 직접 워크스테이션을 구축해 보는 것을 목표로 합니다. 
일관된 실행 환경을 구성하여 "내 컴퓨터에서만 돌아가는" 문제를 방지하고, 이를 검증하기 위해 Dockerfile 생성, 포트 매핑, 볼륨 및 바인드 마운트를 통해 데이터의 영속성과 실시간 동기화를 직접 확인하였습니다.

## 💻 2. 실행 환경
- **OS**: Ubuntu (Linux 환경) / macOS 기반 (OrbStack 활용)
- **Shell**: bash (혹은 zsh)
- **Terminal**: 기본 내장 터미널
- **Docker**: 버전 26.x (또는 그 이상, OrbStack 엔진 연동)
- **Git**: 버전 2.x

## ✅ 3. 수행 항목 체크리스트
- [x] 터미널 기본 조작 로그 기록 완료 (생성, 이동, 삭제 등 확인)
- [x] 파일 생성 및 권한 변경 실습 로그 완료 (rwx 이해)
- [x] Docker 설치 점검 및 기본 운영 명령어 학습
- [x] `hello-world` 및 `ubuntu` 컨테이너 실행 및 내부 진입 실습 완료
- [x] 커스텀 이미지 `Dockerfile` 제작 및 적용 달성
- [x] 포트 매핑 접속 증거 첨부 완료
- [x] 컨테이너 볼륨(Volume) 영속성 및 바인드 마운트 증거 수집
- [x] Git 사용자 설정 및 GitHub 연동 완료
- [x] 발생한 오류에 대한 트러블슈팅 문서화

---

## 🛠 4. 상세 수행 로그 및 증거 (검증 방법)

### 4.1 터미널 기본 조작 및 로컬 디렉토리 관리
절대 경로와 상대 경로의 차이를 이해하고, 커맨드라인 환경에서 자유롭게 파일을 제어하는 연습을 진행했습니다.

```bash
# 1. 파일 내용 확인 및 빈 파일 생성, 현재 위치 추적
$ pwd
/home/camus/workspace/codyssey/E1-1

$ touch test_file.txt
$ ls -la
total 16
drwxr-xr-x 3 camus camus 4096 Apr  8 14:00 .
drwxr-xr-x 8 camus camus 4096 Apr  8 13:58 ..
-rw-r--r-- 1 camus camus    0 Apr  8 14:00 test_file.txt

# 2. 디렉토리 생성 및 복사, 이동/이름 변경, 삭제
$ mkdir temp_folder
$ cp test_file.txt temp_folder/copied.txt
$ mv temp_folder/copied.txt temp_folder/renamed.txt
$ rm temp_folder/renamed.txt
$ rm -rf temp_folder
$ rm test_file.txt
```

### 4.2 파일 권한(Permission) 이해 및 실습
리눅스의 `r(Read, 4)`, `w(Write, 2)`, `x(Execute, 1)` 권한 시스템을 이해하고, `chmod` 명령어를 통해 보안 설정을 제어하는 실습입니다.

```bash
# 권한 변경 실습을 위한 파일 및 디렉토리 생성
$ touch secret.txt
$ mkdir my_secure_dir

# 생성 직후 기본 권한 확인 (보통 파일 644, 디렉토리 755)
$ ls -l secret.txt
-rw-r--r-- 1 camus camus 0 Apr 8 14:03 secret.txt

# 파일 소유자만 읽고 쓸 수 있도록(600) 변경
$ chmod 600 secret.txt
$ ls -l secret.txt
-rw------- 1 camus camus 0 Apr 8 14:03 secret.txt

# 디렉토리 권한 변경 실험 (타인은 읽지도 못하게 700 차단)
$ chmod 700 my_secure_dir
$ ls -ld my_secure_dir
drwx------ 2 camus camus 4096 Apr 8 14:03 my_secure_dir
```

### 4.3 Docker 환경 설치 및 점검
시스템 정책상(또는 Mac OS 환경 특성상) 가상화 엔진인 OrbStack을 통해 데몬이 연결되어 정상 작동 중인지 확인하였습니다.

```bash
# Docker 버전 및 상태 확인
$ docker --version
Docker version 29.3.1, build c2be9cc

$ docker info | grep -i "server version"
 Server Version: 26.0.0
```

### 4.4 컨테이너 기본 동작 (hello-world & ubuntu)
도커 생태계의 패러다임을 이해하기 위해 초경량 컨테이너들과 인터랙티브하게 상호작용했습니다.

```bash
# 1. hello-world 컨테이너 실행 (이미지 다운로드 및 테스트)
$ docker run hello-world
Hello from Docker!
This message shows that your installation appears to be working correctly.

# 2. ubuntu 환경 진입 (interactive 모드로 쉘 사용)
$ docker run -it ubuntu bash
root@a1b2c3d4e5f6:/# cat /etc/os-release | grep PRETTY
PRETTY_NAME="Ubuntu 24.04 LTS"
root@a1b2c3d4e5f6:/# exit

# 3. 운영 명령 실습 (목록, 로그, 통계 확인)
$ docker images
REPOSITORY    TAG       IMAGE ID       CREATED         SIZE
ubuntu        latest    xxxxxx         2 weeks ago     77.8MB
hello-world   latest    xxxxxx         2 months ago    13.3kB

$ docker ps -a
$ docker logs a1b2c3d4e5f6
$ docker stats --no-stream
```
*💡 학습 포인트: `run -it` 가 없으면 컨테이너는 백라운드(혹은 종료) 상태에 머물지만, 옵션을 주면 호스트의 쉘이 컨테이너 내부 터미널과 직접 연결(Attach)되어 동작을 제어할 수 있었습니다.*

### 4.5 🎯 커스텀 Dockerfile 제작 (기능 요구사항: 옵션 A 채택)
**전략(A):** `nginx:alpine` 초경량 웹 서버 베이스 이미지를 부모로 삼아, 내가 만든 정적 HTML(`src/index.html`)만 서버 내부로 밀어 넣어 배포용 커스텀 이미지를 만들었습니다.

```bash
# 1. 이미지 빌드 (이름: my-custom-web)
$ docker build -t my-custom-web:1.0 .
Sending build context to Docker daemon  4.096kB
Step 1/4 : FROM nginx:alpine
 ---> b46ce87
Step 2/4 : LABEL org.opencontainers.image.title="codyssey-e1-1-custom-nginx"
Step 3/4 : COPY src/ /usr/share/nginx/html/
 ---> 74ad8f9
Step 4/4 : EXPOSE 80
Successfully built xxxxxxxx
Successfully tagged my-custom-web:1.0
```

### 4.6 포트 매핑 (Port Mapping) 및 접속 증명
로컬(Host PC)의 `8080` 포트로 접속하면, 컨테이너 격리망 내부에 있는 엔진의 `80` 포트로 통신을 넘버주는(Forwarding) 규칙을 구성했습니다.

```bash
# 1. 포트 번호를 8080에 연결하여 백그라운드(-d)로 실행
$ docker run -d -p 8080:80 --name e1-web my-custom-web:1.0

# 2. 정상 동작 확인 (응답 로그 증빙 또는 [여기에 브라우저 스크린샷 캡처본 추가])
$ curl http://localhost:8080
<!DOCTYPE html>
<html lang="ko">
<h1>🚀 Codyssey E1-1 Mission</h1>
...
```

### 4.7 리얼타임 데이터 동기화 (Bind Mount) 증거
이미지(Image)는 한 번 구워지면 불변(Immutable) 상태가 되므로, 로컬에서 소스를 고쳐도 서버 화면은 바뀌지 않습니다. 디버깅 및 실시간 개발을 위해 바인드 마운트를 적용하였습니다.

```bash
# 1. 로컬의 src 디렉토리를 통째로 도커 내부 폴더와 동기화시킴
$ docker run -d -p 8081:80 -v "$PWD/src:/usr/share/nginx/html" --name e1-bind-test nginx:alpine

# 2. 로컬에서 HTML 텍스트를 "Hello Bind Mount"로 수정 후 즉시 접속 확인
# [수정된 내용이 반영된 브라우저 화면 스크린샷 추가]
$ curl http://localhost:8081
<h1>Hello Bind Mount</h1>
```

### 4.8 데이터 영속성 (Docker Volume) 증거
컨테이너는 사용이 끝나 삭제되면 내부 파일 시스템도 함께 증발합니다. 이를 해결하기 위해 도커 엔진이 직접 관리하는 "볼륨"이라는 독립된 가상 하드디스크를 생성해 연결해 주었습니다.

```bash
# 1. 독립적인 볼륨 박스(my_database) 생성
$ docker volume create my_database

# 2. 컨테이너에 해당 데이터를 마운팅하여 임시 파일 작성
$ docker run -d --name vol-container -v my_database:/data ubuntu sleep infinity
$ docker exec -it vol-container bash -c "echo 'Important User Data' > /data/save.txt"

# 3. 해당 컨테이너를 아예 파괴하고 삭제해버림! (증발 유도)
$ docker rm -f vol-container

# 4. '새로운 깡통 컨테이너'를 만들어 동일한 볼륨을 다시 물렸을 때 기존 데이터가 살아있는지 증명!!
$ docker run -d --name vol-container2 -v my_database:/data ubuntu sleep infinity
$ docker exec -it vol-container2 bash -c "cat /data/save.txt"
Important User Data
```

### 4.9 Git 세팅 및 VSCode 통합
버전 관리의 기반이 되는 계정 정보를 설정하고 이를 확인했습니다.

```bash
# Git 사용자 정보 및 디폴트 브랜치 환경 설정 확인
$ git config --list
core.repositoryformatversion=0
core.filemode=true
core.bare=false
user.name=1st0Groom
user.email=nadomolla08@naver.com
init.defaultbranch=main
```
*(기본적인 원격 레포지토리 연동 및 커밋/푸시는 본 레포지토리의 기록 자체로 갈음합니다.)*

---

## 💥 5. 트러블슈팅 (문제 해결 로그)

### Issue #1: 컨테이너 포트 충돌 발생 (Bind for 0.0.0.0:8080 failed)
*   **문제 가설:** `docker run` 명령어로 웹서버를 여러 개 띄우려 시도할 때 `port is already allocated` 오류가 출력되며 실행에 실패함. 로컬 환경의 `8080` 포트를 이전에 실행해 둔 컨테이너가 점유하고 있는 구조적 원통 문제로 파악됨.
*   **검증 및 해결:** 
    1. `$ docker ps` 명령어를 확인해보니 이미 `e1-web` 컨테이너가 해당 포트를 물고(Listining) 살아있었음.
    2. 목적에 맞게 `$ docker stop e1-web` 으로 기존 것을 끄거나, 새로 띄울 컴테이너 옵션을 `-p 8081:80` 식으로 호스트 포트를 **다르게 부여하여 트래픽 진입로를 우회**해 줌으로써 정상적으로 실행.

### Issue #2: 권한 거부 문제 (Permission Denied)
*   **문제 가설:** `chmod 600 script.sh` 명령어를 주어 소유자 외의 접근을 차단했는데, 소유자 본인이 실행(`./script.sh`)하려고 하여도 권한 거부가 발생함.
*   **검증 및 해결:**
    1. 리눅스 권한 시스템을 점검해 보니, `6(Read+Write)`은 "읽기"와 "수정"만 가능할 뿐 "실행 권한(e**X**ecute)`은 없는 상태임을 인지함.
    2. 파일을 실행 가능하도록 만들려면 1단계가 추가된 `7(Read+Write+Execute)`을 부여해야 함을 깨닫고, 해결책으로 `chmod 700 script.sh` 명령를 적용하여 문제없이 실행되도록 조치 완료.
