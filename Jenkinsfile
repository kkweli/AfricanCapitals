pipeline {
    agent any

    environment {
        DOCKERHUB_REPO = 'kkweli25/kkweli'
        IMAGE_TAG = 'latest'
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
                        withCredentials([usernamePassword(
                            credentialsId: 'docker-hub-login',
                            usernameVariable: 'DOCKER_USER',
                            passwordVariable: 'DOCKER_PASS'
                        )]) {
                            bat """
                                docker login -u %DOCKER_USER% -p %DOCKER_PASS%
                                docker build -t ${DOCKERHUB_REPO}:${IMAGE_TAG} .
                            """
                        }
                    }
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: 'docker-hub-login',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        bat """
                            docker login -u %DOCKER_USER% -p %DOCKER_PASS%
                            docker push ${DOCKERHUB_REPO}:${IMAGE_TAG}
                        """
                    }
                }
            }
        }

        stage('Deploy to Local Docker Instance') {
            steps {
                script {
                    bat """
                        docker pull ${DOCKERHUB_REPO}:${IMAGE_TAG} || echo "Image pull failed, using local image."
                        docker stop african-capitals-api || echo "Container not running."
                        docker rm african-capitals-api || echo "Container not found."
                        docker run -d --name african-capitals-api -p 8000:8000 ${DOCKERHUB_REPO}:${IMAGE_TAG}
                        
                        echo "Waiting for container to initialize..."
                        timeout /t 30 /nobreak
                        echo "Container logs:"
                        docker logs african-capitals-api
                        curl -v --retry 5 --retry-delay 10 http://localhost:8000/health || (
                            echo "Health check failed" && 
                            docker logs african-capitals-api && 
                            exit 1
                        )
                    """
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}