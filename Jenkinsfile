pipeline {
    agent { label 'main-executor' }  // Runs on a Windows agent with Docker installed

    environment {
        DOCKERHUB_REPO = 'kkweli25/kkweli'
        IMAGE_TAG = "${env.BUILD_NUMBER}"  // Unique tag using build number
        CONTAINER_NAME = 'african-capitals-api'
        HOST_PORT = '8000'
        CONTAINER_PORT = '8000'
    }

    stages {
        stage('Checkout Source') {
            steps {
                git url: 'https://github.com/kkweli/AfricanCapitals.git', branch: 'main'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    retry(3) {
                        bat """
                            docker build -t ${DOCKERHUB_REPO}:${IMAGE_TAG} .
                        """
                    }
                }
            }
        }

        stage('Docker Login') {
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: 'docker-hub-login',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        bat """
                            echo %DOCKER_PASS% | docker login -u %DOCKER_USER% --password-stdin
                        """
                    }
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    bat """
                        docker push ${DOCKERHUB_REPO}:${IMAGE_TAG}
                    """
                }
            }
        }

        stage('Prepare Docker Compose Environment') {
            steps {
                script {
                    // Create .env file for Docker Compose
                    bat """
                        @echo off
                        echo IMAGE_TAG=${IMAGE_TAG} > .env.deploy
                        echo DOCKERHUB_REPO=${DOCKERHUB_REPO} >> .env.deploy
                    """
                    
                    // Update docker-compose.yml to use the built image
                    bat """
                        @echo off
                        (
                            echo version: '3.8'
                            echo.
                            echo services:
                            echo   api:
                            echo     image: ${DOCKERHUB_REPO}:${IMAGE_TAG}
                            echo     container_name: ${CONTAINER_NAME}
                            echo     ports:
                            echo       - "${HOST_PORT}:${CONTAINER_PORT}"
                            echo     env_file:
                            echo       - .env
                            echo     healthcheck:
                            echo       test: ["CMD", "curl", "-f", "http://localhost:${CONTAINER_PORT}/health"]
                            echo       interval: 30s
                            echo       timeout: 10s
                            echo       retries: 3
                            echo       start_period: 5s
                            echo     restart: unless-stopped
                        ) > docker-compose.deploy.yml
                    """
                }
            }
        }
        
        stage('Deploy with Docker Compose') {
            steps {
                script {
                    // Deploy using Docker Compose
                    bat """
                        @echo off
                        docker-compose -f docker-compose.deploy.yml --env-file .env.deploy down
                        docker-compose -f docker-compose.deploy.yml --env-file .env.deploy up -d
                    """
                    
                    // Health check loop
                    bat """
                        @echo off
                        setlocal enabledelayedexpansion
                        
                        set MAX_RETRIES=15
                        set RETRY_DELAY=5
                        set RETRY_COUNT=0

                        :healthcheck_retry
                        curl.exe --max-time 10 http://localhost:${HOST_PORT}/health
                        if %errorlevel%==0 (
                            echo Health check passed
                            goto :end
                        )

                        set /a RETRY_COUNT+=1
                        if %RETRY_COUNT% geq %MAX_RETRIES% (
                            echo Health check failed after %MAX_RETRIES% attempts
                            echo Container logs:
                            docker-compose -f docker-compose.deploy.yml logs
                            exit /b 1
                        )

                        echo Attempt %RETRY_COUNT%/%MAX_RETRIES%: Application not ready, retrying in %RETRY_DELAY%s
                        timeout /t %RETRY_DELAY% /nobreak >nul
                        goto :healthcheck_retry
                        
                        :end
                        endlocal
                    """
                }
            }
        }
        
        stage('Cleanup Old Images') {
            steps {
                script {
                    // Remove old images to save disk space
                    bat """
                        @echo off
                        setlocal enabledelayedexpansion
                        
                        REM -- Remove all but the last two images for this repo
                        set COUNT=0
                        for /f "skip=1 tokens=1" %%i in ('docker images --format "{{.ID}} {{.Repository}}:{{.Tag}} {{.CreatedAt}}" --filter=reference=${DOCKERHUB_REPO}:* --no-trunc ^| sort /R') do (
                            set /a COUNT+=1
                            if !COUNT! gtr 2 (
                                echo Removing old image ID: %%i
                                docker rmi -f %%i
                            )
                        )
                        endlocal
                    """
                }
            }
        }
    
    }

    post {
        success {
            echo "Pipeline completed successfully. Application is running at http://localhost:${HOST_PORT}"
        }
        failure {
            echo "Pipeline failed. Check logs for details."
            script {
                bat "docker-compose -f docker-compose.deploy.yml logs || echo 'No container logs available.'"
            }
        }
        always {
            // Archive the deployment files for reference
            archiveArtifacts artifacts: 'docker-compose.deploy.yml,.env.deploy', allowEmptyArchive: true
            cleanWs()
        }
    }
}