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
                            docker login -u %DOCKER_USER% -p %DOCKER_PASS%
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

        stage('Deploy to Local Docker Instance') {
            steps {
                script {
                    bat """
                        @echo off
                        setlocal enabledelayedexpansion

                        :: Cleanup any existing container first
                        echo Stopping and removing previous container...
                        docker stop african-capitals-api >nul 2>&1
                        docker rm african-capitals-api >nul 2>&1

                        :: Wait for port to become free
                        set PORT_CHECK_RETRIES=5
                        set PORT_CHECK_DELAY=5
                        set PORT_CHECK_COUNT=0

                        :port_check_loop
                        netstat -ano | findstr :8000 >nul
                        if !errorlevel! equ 0 (
                            if !PORT_CHECK_COUNT! geq !PORT_CHECK_RETRIES! (
                                echo ERROR: Port 8000 still in use after !PORT_CHECK_RETRIES! attempts
                                exit 1
                            )
                            echo Port 8000 in use, retry !PORT_CHECK_COUNT!/!PORT_CHECK_RETRIES!...
                            timeout /t !PORT_CHECK_DELAY! >nul
                            set /a PORT_CHECK_COUNT+=1
                            goto port_check_loop
                        )

                        :: Start new container with restart policy
                        echo Starting new container...
                        docker run -d \\
                            --name ${CONTAINER_NAME}  \\
                            --restart unless-stopped \\
                            -p ${HOST_PORT}:${CONTAINER_PORT} \\
                            ${DOCKERHUB_REPO}:${IMAGE_TAG}

                        :: Health check with increased timeout and retries
                        set MAX_RETRIES=15
                        set RETRY_DELAY=10
                        set RETRY_COUNT=0

                        :health_check_loop
                        curl.exe -sS -m 30 http://localhost:8000/health >nul
                        if !errorlevel! equ 0 (
                            echo Health check successful
                            exit 0
                        )

                        if !RETRY_COUNT! geq !MAX_RETRIES! (
                            echo ERROR: Health check failed after !MAX_RETRIES! attempts
                            echo Container logs:
                            docker logs african-capitals-api
                            exit 1
                        )

                        echo Health check attempt !RETRY_COUNT!/!MAX_RETRIES! failed
                        timeout /t !RETRY_DELAY! >nul
                        set /a RETRY_COUNT+=1
                        goto health_check_loop
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
                bat "docker logs ${CONTAINER_NAME} || echo 'No container logs available.'"
            }
        }
        always {
            cleanWs()
        }
    }
}