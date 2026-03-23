pipeline {
    agent any

    environment {
        // 배포가 실행될 폴더 위치를 환경 변수로 지정합니다.
        PROJECT_DIR = '.' 
    }

    stages {
        stage('Checkout') {
            steps {
                // 제어판(SCM) 깃랩 버전에 맞는 최신 코드를 당겨옵니다.
                checkout scm
            }
        }


        stage('Build docker-compose') {
            steps {
                script {
                    echo "Provisioning .env configuration securely..."
                    sh '''
                    # 기존처럼 하드코딩하지 않고, 젠킨스 서버 내부에 안전하게 격리된 .env 파일을 복사해옵니다.
                    cp /var/jenkins_home/secrets_safe/.env ./.env
                    '''
                    
                    echo "Building Docker Images..."
                    sh '''
                    # Dockerfile(프론트, 백, AI) 이미지 빌드
                    docker-compose build
                    '''
                }
            }
        }

        stage('Deploy (Run)') {
            steps {
                script {
                    echo "Deploying new infrastructure..."
                    sh '''
                    # 백그라운드(-d)로 모든 서비스를 실행
                    docker-compose up -d
                    '''
                }
            }
        }
    }
}
