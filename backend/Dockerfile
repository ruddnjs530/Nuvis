FROM node:20-alpine

WORKDIR /app

# npm install 선배치 (캐싱 활용)
COPY package*.json ./
RUN npm install

# 소스 전체 복사
COPY . .

# backend 실행 포트 노출
EXPOSE 8081

# 서버 구동 명령어
CMD ["npm", "start"]
