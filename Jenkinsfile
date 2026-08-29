pipeline {
    agent {
        docker {
            // No --network host: the app and the tests both run inside
            // this same container, so they only ever need to talk to each
            // other over the container's own loopback. --network host
            // shares the *Jenkins host's* network namespace instead, and
            // on a shared host that already has something bound to
            // 127.0.0.1:8000, that means "our" port 8000 is actually
            // someone else's service — which is exactly what happened
            // here (every request came back 401 from an unrelated app).
            image 'mcr.microsoft.com/playwright/python:v1.48.0-jammy'
            args '-u root'
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
        stage('Clean previous reports') {
            steps {
                // The workspace persists across builds, and reports/ was
                // never cleared between runs — archiveArtifacts then
                // re-archived every report from every past build each
                // time, burying the current run's results in old ones
                // (including stale screenshots/videos from old failures).
                sh 'rm -rf reports'
            }
        }

        stage('Install dependencies') {
            steps {
                sh '''
                    pip install --no-cache-dir -r requirements.txt
                    # playwright is pinned to match the Docker image's tag (v1.48.0-jammy),
                    # which ships browser binaries baked in for that exact Playwright
                    # version. Without the pin, pip grabs the latest playwright package,
                    # whose client expects browsers this older image doesn't have —
                    # "BrowserType.launch: Executable doesn't exist" at test time.
                    pip install --no-cache-dir pytest pytest-playwright pytest-html requests "playwright==1.48.0"
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

        stage('Run Database Tests') {
            steps {
                sh 'python cli.py -m db_test --start'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
            // Native Jenkins test-trend dashboard: reads every stage's
            // junit.xml (each report_dir now unique per stage/module —
            // see utils/config.py) and aggregates pass/fail history across
            // builds on the job's own page, no extra infra needed.
            junit testResults: 'reports/**/junit.xml', allowEmptyResults: true
            sh '''
                pkill -f uvicorn || true
                pkill -f http.server || true
            '''
        }
    }
}
