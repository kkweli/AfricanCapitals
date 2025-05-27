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
                        powershell -Command "if (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue) { Write-Output 'Port 8000 is in use'; exit 1 }"
                        echo "Port 8000 is available"
                        echo "Pulling image..."
                        docker pull ${DOCKERHUB_REPO}:${IMAGE_TAG}
                        echo "Stopping existing container..."
                        docker stop ${CONTAINER_NAME} || echo "Container not running."
                        echo "Removing existing container..."
                        docker rm ${CONTAINER_NAME} || echo "Container not found."
                        echo "Running new container..."
                        docker run -d --name ${CONTAINER_NAME} -p ${HOST_PORT}:${CONTAINER_PORT} ${DOCKERHUB_REPO}:${IMAGE_TAG}
                        echo "Waiting for container to initialize..."
                        timeout /t <seconds> [/nobreak]
                        echo "Container logs:"
                        docker logs ${CONTAINER_NAME}
                        echo "Performing health check..."
                        curl -v --retry 5 --retry-delay 30 http://localhost:${HOST_PORT}/health || (
                            echo "Health check failed"
                            docker logs ${CONTAINER_NAME}
                            exit 1
                        )
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