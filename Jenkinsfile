pipeline {
    agent {
        docker {
            image 'mcr.microsoft.com/playwright/python:v1.48.0-jammy'
            args '--network host -u root'
        }
    }

    environment {
        // Point the test suites at the app this pipeline just built and
        // started locally, not the deployed Render app (utils/config.py
        // defaults there for local-dev convenience, but CI must test its
        // own build).
        FRONTEND_URL = 'http://127.0.0.1:8000'
        API_URL = 'http://127.0.0.1:8000'
    }

    stages {
        stage('Install dependencies') {
            steps {
                sh '''
                    pip install --no-cache-dir -r requirements.txt
                    pip install --no-cache-dir pytest pytest-playwright pytest-html requests
                '''
            }
        }

        stage('Start App') {
            steps {
                sh '''
                    nohup python -m uvicorn database.api:app --port 8000 > backend.log 2>&1 &
                    sleep 3
                    cd frontend && nohup python -m http.server 5500 > ../frontend.log 2>&1 &
                    sleep 2
                '''
            }
        }

        stage('Run API Tests') {
            steps {
                sh 'python cli.py -m api_test --start'
            }
        }

        stage('Run UI Tests') {
            steps {
                sh 'python cli.py -m ui_test --start'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
            sh '''
                pkill -f uvicorn || true
                pkill -f http.server || true
            '''
        }
    }
}
