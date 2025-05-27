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

                        REM -- Try to stop the container
                        docker stop ${CONTAINER_NAME}
                        if errorlevel 1 (
                            echo No running container named '${CONTAINER_NAME}' to stop.
                        ) else (
                            echo Stopped existing container '${CONTAINER_NAME}'.
                        )

                        REM -- Try to remove the container
                        docker rm ${CONTAINER_NAME}
                        if errorlevel 1 (
                            echo No container named '${CONTAINER_NAME}' to remove.
                        ) else (
                            echo Removed container '${CONTAINER_NAME}'.
                        )

                        REM -- Try to remove the image
                        docker rmi ${DOCKERHUB_REPO}:${IMAGE_TAG}
                        if errorlevel 1 (
                            echo No image '${DOCKERHUB_REPO}:${IMAGE_TAG}' to remove.
                        ) else (
                            echo Removed image '${DOCKERHUB_REPO}:${IMAGE_TAG}'.
                        )

                        REM -- Start new container
                        docker run -d --name ${CONTAINER_NAME} -p ${HOST_PORT}:${CONTAINER_PORT} ${DOCKERHUB_REPO}:${IMAGE_TAG}

                        REM -- Health check loop
                        set MAX_RETRIES=15
                        set RETRY_DELAY=5
                        set RETRY_COUNT=0

                        :retry_loop
                        curl.exe -v --max-time 10 http://localhost:${HOST_PORT}/health >nul
                        if !errorlevel! equ 0 (
                            echo Health check passed
                            exit 0
                        )

                        if !RETRY_COUNT! geq !MAX_RETRIES! (
                            echo Health check failed after !MAX_RETRIES! attempts
                            echo Container logs:
                            docker logs ${CONTAINER_NAME}
                            exit 1
                        )

                        echo Attempt !RETRY_COUNT!/!MAX_RETRIES!: Application not ready
                        timeout /t !RETRY_DELAY! /nobreak >nul
                        set /a RETRY_COUNT+=1
                        goto retry_loop
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