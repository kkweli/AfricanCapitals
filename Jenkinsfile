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
                    // Compute previous tag; Jenkinsfile Groovy uses Integer arithmetic
                    def prevTag = ""
                    if (env.BUILD_NUMBER.toInteger() > 1) {
                        prevTag = (env.BUILD_NUMBER.toInteger() - 1).toString()
                    }

                    // Build deploy script with optional previous image deletion
                    def deployScript = """
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
                    """
                    if (prevTag != "") {
                        deployScript += """
                        REM -- Try to remove the previous image
                        docker rmi ${DOCKERHUB_REPO}:${prevTag}
                        if errorlevel 1 (
                            echo No previous image '${DOCKERHUB_REPO}:${prevTag}' to remove.
                        ) else (
                            echo Removed previous image '${DOCKERHUB_REPO}:${prevTag}'.
                        )
                        """
                    } else {
                        deployScript += """
                        REM -- First build, no previous image to remove.
                        """
                    }
                    deployScript += """
                        REM -- Start new container
                        docker run -d --name ${CONTAINER_NAME} -p ${HOST_PORT}:${CONTAINER_PORT} ${DOCKERHUB_REPO}:${IMAGE_TAG}

                        REM -- Simple health check loop
                        set MAX_RETRIES=15
                        set RETRY_DELAY=5
                        set RETRY_COUNT=0

                        :healthcheck_retry
                        curl.exe --max-time 10 http://localhost:%HOST_PORT%/health >nul 2>&1
                        if %errorlevel%==0 (
                            echo Health check passed
                            exit /b 0
                        )

                        set /a RETRY_COUNT+=1
                        if %RETRY_COUNT% geq %MAX_RETRIES% (
                            echo Health check failed after %MAX_RETRIES% attempts
                            echo Container logs:
                            docker logs %CONTAINER_NAME%
                            exit /b 1
                        )

                        echo Attempt %RETRY_COUNT%/%MAX_RETRIES%: Application not ready, retrying in %RETRY_DELAY%s
                        timeout /t %RETRY_DELAY% /nobreak >nul
                        goto healthcheck_retry
                    """

                    // Actually call BAT script
                    bat(deployScript)
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