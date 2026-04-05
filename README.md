# 코디세이(Codyssey) 개발 워크스테이션 구축 프로젝트

## 1. 프로젝트 개요
- **목적**: 로컬 개발 환경 세팅, 재현 가능한 실행 환경 공유, 협업 기반 소스코드 관리를 위한 워크스테이션 구축
- **핵심 기술**: Linux CLI, Docker, Git / GitHub

## 2. 실행 환경
- **Host OS**: Ubuntu 24.04.4 LTS
- **Shell / Terminal**: bash
- **Docker Version**: Docker version 29.3.1, build c2be9cc
- **Git Version**: git version 2.43.0

## 3. 학습 목표 달성 (개념 정리)

- **절대 경로와 상대 경로의 차이**:
  - **절대 경로**: 파일 시스템의 최상위 경로(`/`)부터 시작해서 특정 파일까지 도달하는 경로를 기록합니다.
  - **상대 경로**: 현재 내가 위치한 디렉토리를 기준으로 타겟 파일의 위치를 나타내는 경로입니다.

- **파일 권한(r/w/x)과 755/644의 의미**:
  - `r`(read), `w`(write), `x`(execute)의 약자로 각각 읽기, 쓰기, 실행 권한을 의미합니다. (`r=4`, `w=2`, `x=1`로 세 권한의 합으로 표현)
  - 세자리 숫자는 각각 **유저 권한(100의 자리)**, **그룹 권한(10의 자리)**, **기타 사용자 권한(1의 자리)**을 뜻합니다.

- **포트 매핑이 필요한 이유**:
  - 외부 네트워크에서 내부 네트워크 상 기기(컨테이너 등)에 접속할 수 있도록 통로를 열어주는 기술입니다 (포트 포워딩). IP 주소가 아파트 단지 주소라면, 포트 번호는 동/호수와 같습니다.

- **Docker 볼륨(영속 데이터)의 개념**:
  - 도커는 컨테이너를 삭제하면 그 안에서 생성된 모든 데이터가 소멸합니다. 이를 방지하고 데이터를 보존하기 위해 **데이터 영속성**을 부여하며, 주로 볼륨(Volume)을 통해 구현합니다.
  - 동작 원리는 호스트 OS의 특정 디렉토리를 컨테이너 내부의 디렉토리와 연결(Mount)하는 방식입니다. 볼륨 외에도 Bind Mount, tmpfs mount 등을 활용할 수 있습니다.

- **Git과 GitHub의 역할 차이**:
  - **Git**: 소스 코드 변경 이력을 관리하는 분산 버전 관리 시스템 소프트웨어로, 로컬 환경에서 구축하여 인터넷 연결 없이 사용할 수 있습니다.
  - **GitHub**: 내 컴퓨터에 있는 Git 저장소를 인터넷(클라우드) 상에 올려서 다른 사람들과 공유하고 협업할 수 있는 웹 플랫폼 서비스입니다.

## 4. 수행 항목 체크리스트
- [x] 터미널 기본 조작 및 작업 디렉토리 구성
- [x] 파일 및 디렉토리 권한 변경 실습
- [x] Docker 설치 확인 및 데몬 동작 점검
- [x] `hello-world` 및 `ubuntu` 컨테이너 실행/진입 실습
- [x] 커스텀 Dockerfile 작성 및 빌드
- [x] 포트 매핑을 통한 접속 증명
- [x] 바인드 마운트를 활용한 변경 사항 실시간 반영 검증
- [x] 도커 볼륨(Volume)을 활용한 데이터 영속성 검증
- [x] Git 환경 설정 및 GitHub/VSCode 연동 완료


### 4.1. 터미널 조작 및 권한 변경 실습

```bash
$ mkdir -p ~/workspace/codyssey
$ cd ~/workspace/codyssey
$ mkdir src
$ touch src/index.html

$ ls -la src/
➜  codyssey git:(main) ✗ ls -al src/
합계 16
drwxrwxr-x 2 camus camus  4096 Mar 31 17:41 .
drwxrwxr-x 4 camus camus  4096 Apr  1 13:49 ..
-rw-r--r-- 1 camus camus   123 Apr  1 15:57 index.html

$ chmod 755 src/index.html
$ ls -l src/index.html
➜  codyssey git:(main) ✗ chmod 755 src/index.html                      
➜  codyssey git:(main) ✗ ls -l src/index.html 
-rwxr-xr-x 1 camus camus 123 Apr  1 15:57 src/index.html

$ chmod 644 src/index.html
$ ls -l src/index.html
➜  codyssey git:(main) ✗ chmod 644 src/index.html                      
➜  codyssey git:(main) ✗ ls -l src/index.html 
-rw-r--r-- 1 camus camus 123 Apr  1 15:57 src/index.html
```

### 4.2. git 설정 및 초기화

```bash
$ git init
$ git config user.name "1st0Groom"
$ git config user.email "nadomolla08@naver.com"
$ git config init.defaultBranch main
$ git config --list

core.repositoryformatversion=0
core.filemode=true
core.bare=false
core.logallrefupdates=true
user.name=1st0Groom
user.email=nadomolla08@naver.com
init.defaultbranch=main
```

### 4.3. Docker 설치 및 기본 점검

```bash
➜  codyssey git:(main) ✗ docker --version
Docker version 29.3.1, build c2be9cc

➜  codyssey git:(main) ✗ docker info     
Client: Docker Engine - Community
 Version:    29.3.1
 Context:    default
 Debug Mode: false
 Plugins:
  buildx: Docker Buildx (Docker Inc.)
    Version:  v0.31.1
    Path:     /usr/libexec/docker/cli-plugins/docker-buildx
  compose: Docker Compose (Docker Inc.)
    Version:  v5.1.1
    Path:     /usr/libexec/docker/cli-plugins/docker-compose

Server:
 Containers: 1
  Running: 0
  Paused: 0
  Stopped: 1
 Images: 4
 Server Version: 29.3.1
 Storage Driver: overlayfs
  driver-type: io.containerd.snapshotter.v1
 Logging Driver: json-file
 Cgroup Driver: systemd
 Cgroup Version: 2
 Plugins:
  Volume: local
  Network: bridge host ipvlan macvlan null overlay
  Log: awslogs fluentd gcplogs gelf journald json-file local splunk syslog
 CDI spec directories:
  /etc/cdi
  /var/run/cdi
 Swarm: inactive
 Runtimes: io.containerd.runc.v2 runc
 Default Runtime: runc
 Init Binary: docker-init
 containerd version: 301b2dac98f15c27117da5c8af12118a041a31d9
 runc version: v1.3.4-0-gd6d73eb8
 init version: de40ad0
 Security Options:
  apparmor
  seccomp
   Profile: builtin
  cgroupns
 Kernel Version: 6.17.0-19-generic
 Operating System: Ubuntu 24.04.4 LTS
 OSType: linux
 Architecture: x86_64
 CPUs: 16
 Total Memory: 15.03GiB
 Name: camus-ROG-Zephyrus-G14-GA401QM-GA401QM
 ID: 9b064c44-36ae-4bef-af85-9952ed24a37f
 Docker Root Dir: /var/lib/docker
 Debug Mode: false
 Experimental: false
 Insecure Registries:
  ::1/128
  127.0.0.0/8
 Live Restore Enabled: false
 Firewall Backend: iptables
```

### 4.4. 컨테이너 실행 및 기본 운영 실습

```bash
➜  codyssey git:(main) ✗ docker run hello-world

Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/
```

```bash
➜  codyssey git:(main) ✗ docker run -it ubuntu bash 
root@6158c3ebc8bb:/# ls -al
total 56
drwxr-xr-x   1 root root 4096 Apr  2 03:59 .
drwxr-xr-x   1 root root 4096 Apr  2 03:59 ..
-rwxr-xr-x   1 root root    0 Apr  2 03:59 .dockerenv
lrwxrwxrwx   1 root root    7 Apr 22  2024 bin -> usr/bin
drwxr-xr-x   2 root root 4096 Apr 22  2024 boot
drwxr-xr-x   5 root root  360 Apr  2 03:59 dev
drwxr-xr-x   1 root root 4096 Apr  2 03:59 etc
drwxr-xr-x   3 root root 4096 Feb 17 02:09 home
lrwxrwxrwx   1 root root    7 Apr 22  2024 lib -> usr/lib
lrwxrwxrwx   1 root root    9 Apr 22  2024 lib64 -> usr/lib64
drwxr-xr-x   2 root root 4096 Feb 17 02:02 media
drwxr-xr-x   2 root root 4096 Feb 17 02:02 mnt
drwxr-xr-x   2 root root 4096 Feb 17 02:02 opt
dr-xr-xr-x 461 root root    0 Apr  2 03:59 proc
drwx------   2 root root 4096 Feb 17 02:09 root
drwxr-xr-x   4 root root 4096 Feb 17 02:09 run
lrwxrwxrwx   1 root root    8 Apr 22  2024 sbin -> usr/sbin
drwxr-xr-x   2 root root 4096 Feb 17 02:02 srv
dr-xr-xr-x  13 root root    0 Apr  2 03:59 sys
drwxrwxrwt   2 root root 4096 Feb 17 02:09 tmp
drwxr-xr-x  12 root root 4096 Feb 17 02:02 usr
drwxr-xr-x  11 root root 4096 Feb 17 02:09 var

root@6158c3ebc8bb:/# echo "container test" >test.txt
root@6158c3ebc8bb:/# cat test.txt 
container test
root@6158c3ebc8bb:/# exit
exit
```

```bash
➜  codyssey git:(main) ✗ docker ps -a                   
CONTAINER ID   IMAGE          COMMAND                   CREATED             STATUS                         PORTS     NAMES
6158c3ebc8bb   ubuntu         "bash"                    About an hour ago   Exited (0) About an hour ago             crazy_almeida
6ca4396eb1e8   hello-world    "/hello"                  About an hour ago   Exited (0) About an hour ago             eager_hermann
83d1e285f37f   nginx:alpine   "/docker-entrypoint.…"   15 hours ago        Exited (0) 14 hours ago                  my-web-bind
```

```bash
➜  codyssey git:(main) ✗ docker images
IMAGE                ID             DISK USAGE   CONTENT SIZE   EXTRA
hello-world:latest   452a468a4bf9       25.9kB         9.49kB    U   
my-web:1.0           0281eece23fe       92.6MB           26MB        
nginx:alpine         e7257f1ef28b       93.5MB         26.9MB    U   
ubuntu:latest        186072bba1b2        119MB         31.7MB    U   
```

```bash
➜  codyssey git:(main) ✗ docker logs 6158c3ebc8bb
root@6158c3ebc8bb:/# ls -al
total 56
... (생략) ...
drwxrwxrwt   2 root root 4096 Feb 17 02:09 tmp
drwxr-xr-x  12 root root 4096 Feb 17 02:02 usr
drwxr-xr-x  11 root root 4096 Feb 17 02:09 var
root@6158c3ebc8bb:/# echo "container test" >test.txt
root@6158c3ebc8bb:/# cat test.txt 
container test
root@6158c3ebc8bb:/# exit
exit
```

```bash
➜  codyssey git:(main) ✗ docker stats --no-stream
```

### 4.5. 개념 정리: attach vs exec

- **docker attach**: 컨테이너의 메인 프로세스(PID 1)에 직접 연결하여 표준 입출력을 제어합니다. 여기서 작업을 종료(`exit`)하면 메인 프로세스가 종료되므로, **컨테이너 자체도 완전히 종료(Exited)**됩니다.
- **docker exec**: 이미 실행 중인 컨테이너 내부에 새로운 독립적인 프로세스(예: `/bin/bash`)를 생성하여 접속합니다. 여기서 작업을 종료해도 새로 만든 프로세스만 죽을 뿐, 컨테이너의 메인 프로세스는 계속 실행 상태를 유지합니다.

### 4.6. 커스텀 이미지 빌드 및 포트 매핑

```bash
$ echo "<h1>Hello Codyssey! This is my custom Nginx.</h1>" > src/index.html

$ cat << 'EOF' > Dockerfile
FROM nginx:alpine
LABEL maintainer="camus"
LABEL description="Codyssey Custom Nginx Web Server"
COPY src/ /usr/share/nginx/html/
EXPOSE 80
EOF

$ docker build -t my-web:1.0 .
[+] Building 0.1s (7/7) FINISHED                                              docker:default
 => [internal] load build definition from Dockerfile                                    0.0s
 => => transferring dockerfile: 178B                                                    0.0s
 => [internal] load metadata for docker.io/library/nginx:alpine                         0.0s
 => [internal] load .dockerignore                                                       0.0s
 => => transferring context: 2B                                                         0.0s
 => [internal] load build context                                                       0.0s
 => => transferring context: 92B                                                        0.0s
 => [1/2] FROM docker.io/library/nginx:alpine@sha256:e7257f1ef28ba17cf7c248cb8ccf6f0c6  0.0s
 => => resolve docker.io/library/nginx:alpine@sha256:e7257f1ef28ba17cf7c248cb8ccf6f0c6  0.0s
 => CACHED [2/2] COPY src/ /usr/share/nginx/html/                                       0.0s
 => exporting to image                                                                  0.0s
 => => exporting layers                                                                 0.0s
 => => exporting manifest sha256:757579066fdc5a6bcd2baa2492032b453b97d153f5ee06156c069  0.0s
 => => exporting config sha256:ab78261121ee12e395681cc329ee42c85444950bd407c0de1aa086f  0.0s
 => => exporting attestation manifest sha256:9925f9c77269c54910f874d362c11e35f2af0143c  0.0s
 => => exporting manifest list sha256:1a76b400ac2e446790adc4c7d9972c3455502d4a52bb12d0  0.0s
 => => naming to docker.io/library/my-web:1.0                                           0.0s
 => => unpacking to docker.io/library/my-web:1.0  

$ docker run -d -p 8080:80 --name my-web-8080 my-web:1.0
a82c6ac834987e92eb10027ae2eedb0fb48cabdd490b200bf271d27579163be2

$ curl http://localhost:8080
<h1>Hello Codyssey! This is my custom Nginx.</h1>
<img width="748" height="211" alt="스크린샷 2026-03-31 17-47-53" src="https://github.com/user-attachments/assets/659d2561-0405-43e7-8131-7e91f70c1a1b" />
```

### 4.7. Docker 커스텀 이미지 빌드 및 포트 매핑 통신 팩트 체크

```bash
$ echo "<h1>Hello Codyssey! This is my custom Nginx.</h1>" > src/index.html
$ docker build -t my-web:1.0 .
$ docker run -d -p 8090:80 --name my-web-final my-web:1.0

# 서버 정상 응답 확인 (200 OK)
$ curl -I http://localhost:8090
HTTP/1.1 200 OK
Server: nginx/1.29.7
Content-Length: 49
```

### 4.8. 바인드 마운트 (Bind Mount) 실시간 동기화 검증
도커 이미지의 불변성(Immutability)을 극복하고, 호스트 소스 수정 시 컨테이너에 즉시 반영됨을 증명함.

```bash
$ docker run -d -p 8080:80 -v "$PWD/src:/usr/share/nginx/html" --name my-web-bind nginx:alpine

$ echo "<h1>Bind Mount is LIVE!</h1>" > src/index.html
$ curl http://localhost:8080
<h1>Bind Mount is LIVE!</h1>
```

### 4.9. 데이터 영속성 (Docker Volume) 검증
컨테이너 파괴 후에도 호스트 시스템에 마운트된 볼륨의 데이터가 생존함을 증명함.

```bash
$ docker volume create my-data
$ docker run -d --name vol-test -v my-data:/app ubuntu sleep infinity
$ docker exec vol-test sh -c "echo 'Persistence Verified' > /app/result.txt"

$ docker rm -f vol-test
$ docker run --rm -v my-data:/app ubuntu cat /app/result.txt
Persistence Verified
```


## 5. 트러블슈팅

### Case 1: 명령어 입력 중 쉘 줄 바꿈( `\` ) 문법으로 인한 실행 대기
- **문제 상황**: 터미널에서 `wget http://127.0.0.1:8080\` 처럼 명령어를 입력했을 때, 실행되지 않고 `>` 프롬프트만 뜨며 터미널이 멈추는 현상 발생.
- **원인 가설**: 명령어 끝에 입력된 역슬래시(`\`) 기호가 리눅스 쉘 문법상 **'명령어 줄 바꿈(Line Continuation)'**을 의미하기 때문에, 시스템이 추가 명령 입력을 대기하고 있는 상태라고 판단.
- **확인 및 해결**: `Ctrl + C`를 입력하여 대기 상태를 강제 취소한 후, 역슬래시 없이 한 줄로 명령어를 재입력(또는 올바르게 줄 바꿈하여 입력)하여 정상 실행함.

### Case 2: 포트 좀비 현상(`TIME_WAIT`) 및 컨테이너 이름 충돌
- **문제 상황**: 컨테이너를 새로 띄운 후 브라우저와 curl에서 `localhost:8080` 포트로의 접속이 거부되는 현상.
- **원인 가설**: 이전에 실행/종료했던 컨테이너가 삭제되지 않고 이름을 점유하고 있거나, 우분투 커널의 네트워크 스택이 `8080` 포트를 해제하지 못하고 `TIME_WAIT` 상태로 물고 있을 것으로 추정.
- **확인 및 해결**: `docker rm -f $(docker ps -aq)` 명령어로 기존의 컨테이너 객체들을 일괄 파괴하여 충돌을 방지함. 이후 외부 연결 포트를 `8085`, `8090` 등으로 완전히 우회하여 새로 실행한 뒤, `curl -I` 명령어로 `HTTP 200 OK` 통신 성공을 팩트로 검증함.

### Case 3: 클라이언트(브라우저) 캐시로 인한 HTTP 304 렌더링 오류
- **문제 상황**: 터미널 통신 테스트(`curl`)는 정상 응답을 반환하는데, 브라우저 화면은 계속 하얗게 뜨거나 이전 화면이 출력됨.
- **원인 가설**: 브라우저 개발자 도구(F12)의 네트워크 탭 분석 결과, 서버 응답이 `304 Not Modified`로 나타남. 즉, 서버는 정상이지만 브라우저가 변경된 서버의 데이터를 받아오지 않고 로컬의 잘못된 구형 캐시를 렌더링하고 있다고 진단.
- **확인 및 해결**: 브라우저에서 **'캐시 비우기 및 강력 새로고침(`Ctrl + Shift + R`)'**을 수행하여 로컬 캐시를 무효화하고 서버로부터 최신 데이터를 강제 Fetch 하여 화면 출력을 정상화함.

### Case 4: 도커 스냅샷 불변성(Immutability) 오해 및 바인드 마운트로 해결
- **문제 상황**: 서버 인프라는 정상이나, 호스트의 `src/index.html` 파일 내용을 수정해도 웹 브라우저 화면의 코드가 업데이트되지 않음.
- **원인 가설**: Dockerfile의 `COPY` 지시어로 구워진 이미지는 빌드 시점의 '정적 스냅샷'이므로, 실행 중인 컨테이너는 호스트의 파일 변경을 감지할 수 없는 구조(불변성)임을 인지함.
- **확인 및 해결**: 변경 시마다 다시 빌드하는 비효율을 제거하기 위해, `-v "$PWD/src:/usr/share/nginx/html"` 옵션을 추가한 바인드 마운트(Bind Mount) 방식으로 컨테이너를 재실행함. 호스트 소스 디렉토리와 컨테이너 내부를 직접 마운트하여 실시간으로 데이터가 동기화됨을 증명함.
