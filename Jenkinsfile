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

        stage('Deploy to Local Docker Instance') {
            steps {
                script {
                    // Compute previous tag
                    def prevTag = ""
                    if (env.BUILD_NUMBER.toInteger() > 1) {
                        prevTag = (env.BUILD_NUMBER.toInteger() - 1).toString()
                    }

                    // Best practice deployment block
                    def deployScript = """
                        @echo off
                        setlocal enabledelayedexpansion

                        REM -- Ensure Docker network exists
                        docker network inspect african-capitals-net >nul 2>&1
                        if %errorlevel% neq 0 (
                            docker network create african-capitals-net
                            echo Created docker network 'african-capitals-net'
                        ) else (
                            echo Docker network 'african-capitals-net' exists
                        )

                        REM -- Stop and remove any running container with this name
                        docker stop ${CONTAINER_NAME}
                        docker rm ${CONTAINER_NAME}

                    """
                    if (prevTag != "") {
                        deployScript += """
                        REM -- Try to remove the previous image
                        docker rmi ${DOCKERHUB_REPO}:${prevTag}
                        """
                    }

                    deployScript += """
                        REM -- Run the new container
                        docker run -d ^
                        --name ${CONTAINER_NAME} ^
                        --network african-capitals-net ^
                        --restart unless-stopped ^
                        -p ${HOST_PORT}:${CONTAINER_PORT} ^
                        ${DOCKERHUB_REPO}:${IMAGE_TAG}

                        REM -- Health check loop
                        set MAX_RETRIES=15
                        set RETRY_DELAY=5
                        set RETRY_COUNT=0

                        :healthcheck_retry
                        curl.exe --max-time 10 http://localhost:${HOST_PORT}/health
                        if %errorlevel%==0 (
                            echo Health check passed
                            goto cleanup_images
                        )

                        set /a RETRY_COUNT+=1
                        if %RETRY_COUNT% geq %MAX_RETRIES% (
                            echo Health check failed after %MAX_RETRIES% attempts
                            echo Container logs:
                            docker logs ${CONTAINER_NAME}
                            exit /b 1
                        )

                        echo Attempt %RETRY_COUNT%/%MAX_RETRIES%: Application not ready, retrying in %RETRY_DELAY%s
                        timeout /t %RETRY_DELAY% /nobreak >nul
                        goto healthcheck_retry

                        :cleanup_images
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