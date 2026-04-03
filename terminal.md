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
$ git config user.name "camus"
$ git config user.email "nadomolla08@naver.com"
$ git config init.defaultBranch main
$ git config --list

core.repositoryformatversion=0
core.filemode=true
core.bare=false
core.logallrefupdates=true
user.name=camus
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
