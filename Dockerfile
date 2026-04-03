FROM nginx:alpine
LABEL maintainer="camus"
LABEL description="Codyssey Custom Nginx Web Server"
COPY src/ /usr/share/nginx/html/
EXPOSE 80
