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

        stage('Cleanup Legacy Zombies') {
            steps {
                script {
                    echo "Cleaning up old practice containers and orphaned volumes..."
                    sh '''
                    # 1. 기존 컴포즈가 있다면 일단 안전하게 내리기 시도 (실패해도 계속 진행)
                    docker-compose down -v || true
                    
                    # 2. 이전에 수동으로 떠있던 (nuvis 이름이 들어간) 연습용 컨테이너들 무자비하게 강제 킬(Kill) 및 삭제
                    docker ps -a | grep -i "nuvis" | awk '{print $1}' | xargs -r docker rm -f || true
                    docker ps -a | grep -i "smarthome" | awk '{print $1}' | xargs -r docker rm -f || true
                    
                    # 3. 찌꺼기 이미지, 끊어진 볼륨, 남은 캐시들을 단 한 방울도 남기지 않고 포맷 (아주 중요 ⭐️)
                    docker system prune -af --volumes
                    '''
                }
            }
        }

        stage('Build docker-compose') {
            steps {
                script {
                    echo "Building Docker Images..."
                    sh '''
                    # 캐시 없이 깨끗한 상태로 각 Dockerfile(프론트, 백, AI) 이미지를 굽습니다.
                    docker-compose build --no-cache
                    '''
                }
            }
        }

        stage('Deploy (Run)') {
            steps {
                script {
                    echo "Deploying new infrastructure..."
                    sh '''
                    # 백그라운드(-d)로 모든 서비스를 실행합니다.
                    docker-compose up -d
                    '''
                }
            }
        }
    }
}
