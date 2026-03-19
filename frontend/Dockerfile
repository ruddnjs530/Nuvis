# Build stage
FROM node:20-alpine as build
WORKDIR /app

# npm install
COPY package*.json ./
RUN npm install

# 애플리케이션 빌드
COPY . .
RUN npm run build

# Production stage (Nginx)
FROM nginx:alpine
# 빌드된 정적 파일들을 Nginx의 서빙 경로로 복사
COPY --from=build /app/dist /usr/share/nginx/html

# React Router 사용 시 새로고침 오류 방지를 위한 설정 (SPA 라우팅)
RUN echo "server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files \$uri \$uri/ /index.html; \
    } \
}" > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
