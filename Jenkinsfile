pipeline {
    agent any

    stages {
        stage('Pull Code') {
            steps {
                echo 'GitLab에서 최신 코드를 당겨옵니다...'
                checkout scm
            }
        }

        stage('Deploy') {
            steps {
                echo '도커 컴포즈로 실전 배포를 시작합니다...'
                sh 'docker compose up -d --build'
            }
        }
    }
}
