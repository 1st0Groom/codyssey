# 1. Base image (웹 서버 베이스 이미지 사용)
FROM nginx:alpine

# 2. 메타데이터 (선택사항)
LABEL org.opencontainers.image.title="codyssey-e1-1-custom-nginx"
LABEL maintainer="1st0Groom"

# 3. 호스트 시스템의 src 디렉토리를 컨테이너 내부의 Nginx가 참조하는 위치로 복사
# 정적 컨텐츠만 교체하는(A) 방식 채택
COPY src/ /usr/share/nginx/html/

# 4. 외부와 통신할 포트 명시 (문서화 용도)
EXPOSE 80
