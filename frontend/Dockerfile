# 빌드 환경
FROM node:18-alpine AS build
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
# pnpm 설치 후 종속성 설치
RUN npm install -g pnpm && pnpm install
COPY . .
# Vite 빌드 진행
RUN pnpm build

# Nginx 실행 환경
FROM nginx:alpine
# 리액트 정적 파일들을 Nginx 폴더로 복사
COPY --from=build /app/dist /usr/share/nginx/html
# Nginx 설정 파일 덮어쓰기
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"]
