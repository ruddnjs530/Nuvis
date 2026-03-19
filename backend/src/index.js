const express = require('express');
const cors = require('cors');
const mysql = require('mysql2');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 8081; // 기존 스프링부트와 동일한 포트 유지하여 프론트엔드 연동 수월하게 설정

app.use(cors());
app.use(express.json());

// 데이터베이스 연결 풀 설정 (docker-compose의 'db' 서비스 바라보기)
const pool = mysql.createPool({
    host: process.env.DB_HOST || 'db',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || '1234',
    database: process.env.DB_NAME || 'nuvis_db',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// 기본 API 경로 설정
app.get('/api/status', (req, res) => {
    res.json({
        status: 'success',
        message: 'Node.js 백엔드 서버가 정상적으로 구동 중입니다!',
        timestamp: new Date().toISOString()
    });
});

// 데이터베이스 연결 테스트 엔드포인트
app.get('/api/db-test', (req, res) => {
    pool.query('SELECT 1 + 1 AS result', (err, rows) => {
        if (err) {
            return res.status(500).json({ status: 'error', message: 'DB 연결 실패', error: err.message });
        }
        res.json({ status: 'success', message: 'DB 연결 성공!', result: rows[0].result });
    });
});

app.listen(PORT, () => {
    console.log(`===================================================`);
    console.log(`🚀 NUVIS Node.js Backend listening on port: ${PORT}`);
    console.log(`===================================================`);
});
