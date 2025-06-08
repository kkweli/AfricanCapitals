pipeline {
    agent { label 'main-executor' }

    // Environment variables for Docker and deployment
    environment {
        DOCKERHUB_REPO = 'kkweli25/kkweli'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        CONTAINER_NAME = 'african-capitals-api'
        HOST_PORT = '8000'
        CONTAINER_PORT = '8000'
        TRIVY_IMAGE = 'aquasec/trivy:0.51.1'
    }

    stages {
        // Pull Trivy image for vulnerability scanning
        stage('Pull Trivy Image') {
            steps {
                script {
                    // Pull Trivy image only if not present or version changes
                    bat "docker pull %TRIVY_IMAGE%"
                }
            }
        }

        // Checkout source code from GitHub
        stage('Checkout Source') {
            steps {
                git url: 'https://github.com/kkweli/AfricanCapitals.git', branch: 'main'
            }
        }

        // Run Python unit tests before building the Docker image
        stage('Run Tests') {
            steps {
                bat """
                    set PYTHONPATH=%CD%
                    python -m unittest discover -s app/tests -t app
                """
            }
        }

        // Build Docker image for the application
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

        stage('Trivy Scan') {
            steps {
                script {
                    bat """
                        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock ^
                            -v %CD%:/root/.cache/ ^
                            -v %CD%:/scan ^
                            %TRIVY_IMAGE% image --format json --output /scan/trivy-report.json ${DOCKERHUB_REPO}:${IMAGE_TAG}
                    """
                }
                archiveArtifacts artifacts: 'trivy-report.json', allowEmptyArchive: true
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
                    
                    // Detect host timezone and map to IANA timezone
                    def hostTimezone = bat(script: 'powershell -Command "[System.TimeZoneInfo]::Local.Id"', returnStdout: true).trim()
                    def ianaTimezone = "Etc/UTC" // Default fallback
                    
                    // Map Windows timezone ID to IANA timezone
                    def timezoneMap = [
                        "E. Africa Standard Time": "Africa/Nairobi",
                        "Eastern Standard Time": "America/New_York",
                        "Pacific Standard Time": "America/Los_Angeles",
                        "Central European Standard Time": "Europe/Budapest",
                        "GMT Standard Time": "Europe/London",
                        "Tokyo Standard Time": "Asia/Tokyo",
                        "China Standard Time": "Asia/Shanghai",
                        "India Standard Time": "Asia/Kolkata",
                        "Central Standard Time": "America/Chicago",
                        "Mountain Standard Time": "America/Denver",
                        "W. Europe Standard Time": "Europe/Berlin"
                    ]
                    
                    if (timezoneMap.containsKey(hostTimezone)) {
                        ianaTimezone = timezoneMap[hostTimezone]
                    }
                    
                    echo "Host timezone detected: ${hostTimezone}"
                    echo "Using IANA timezone: ${ianaTimezone}"
                    
                    // Create a minimal .env file for the application with dynamic timezone
                    bat """
                        @echo off
                        (
                            echo APP_TITLE=African Capitals API
                            echo APP_DESCRIPTION=Returns the capital cities of African countries grouped by region using the REST Countries public API.
                            echo APP_VERSION=1.2.0
                            echo REST_COUNTRIES_URL=https://restcountries.com/v3.1/region/africa
                            echo LOG_LEVEL=INFO
                            echo EXTERNAL_API_TIMEOUT=10
                            echo TZ=${ianaTimezone}
                            echo CONTAINER_NAME=${CONTAINER_NAME}
                            echo HOST_PORT=${HOST_PORT}
                            echo CONTAINER_PORT=${CONTAINER_PORT}
                        ) > .env
                    """
                    
                    // Update docker-compose.yml to use the built image
                    bat """
                        @echo off
                        (
                            echo services:
                            echo   api:
                            echo     image: ${DOCKERHUB_REPO}:${IMAGE_TAG}
                            echo     container_name: ${CONTAINER_NAME}
                            echo     ports:
                            echo       - "${HOST_PORT}:${CONTAINER_PORT}"
                            echo     env_file:
                            echo       - .env
                            echo     volumes:
                            echo       - /etc/localtime:/etc/localtime:ro
                            echo     healthcheck:
                            echo       test: ["CMD", "curl", "-s", "-f", "http://localhost:${CONTAINER_PORT}/health"]
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
                        echo "Stopping any existing containers..."
                        
                        REM Force stop and remove the container by name regardless of docker-compose
                        echo "Stopping container by name if it exists..."
                        docker stop ${CONTAINER_NAME} 2>nul || echo "Container not running"
                        docker rm ${CONTAINER_NAME} 2>nul || echo "Container not found"
                        
                        REM Now try docker-compose down as well
                        docker-compose -f docker-compose.deploy.yml down || echo "No docker-compose services to stop"
                        
                        echo "Starting new containers..."
                        docker-compose -f docker-compose.deploy.yml up -d
                        
                        echo "Container status:"
                        docker ps
                    """
                    
                    // Health check loop - using a simpler approach for Windows
                    bat """
                        @echo off
                        setlocal enabledelayedexpansion
                        
                        echo "Starting health check..."
                        set MAX_RETRIES=15
                        set RETRY_DELAY=5
                        set RETRY_COUNT=0

                        :healthcheck_retry
                        echo "Attempt !RETRY_COUNT!/%MAX_RETRIES%: Checking health endpoint..."
                        
                        REM Create a temporary file for curl output
                        set TEMP_FILE=%TEMP%\\health_check_response.txt
                        
                        REM Use curl to check the health endpoint and save status code to file
                        curl.exe -s -o nul -w "%%{http_code}" --max-time 10 http://localhost:${HOST_PORT}/health > %TEMP_FILE%
                        
                        REM Read the status code from the file
                        set /p HTTP_STATUS=<%TEMP_FILE%
                        del %TEMP_FILE%
                        
                        echo "Received HTTP status: !HTTP_STATUS!"
                        
                        if "!HTTP_STATUS!"=="200" (
                            echo "Health check passed with HTTP 200 OK!"
                            goto :end
                        )

                        set /a RETRY_COUNT+=1
                        if !RETRY_COUNT! geq %MAX_RETRIES% (
                            echo "Health check failed after %MAX_RETRIES% attempts. Last status: !HTTP_STATUS!"
                            echo "Container logs:"
                            docker logs ${CONTAINER_NAME}
                            exit /b 1
                        )

                        echo "Application not ready (status: !HTTP_STATUS!), retrying in %RETRY_DELAY% seconds..."
                        timeout /t %RETRY_DELAY% /nobreak >nul
                        goto :healthcheck_retry
                        
                        :end
                        echo "Deployment successful with healthy endpoint!"
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
                        
                        echo "Listing current images for repository ${DOCKERHUB_REPO}..."
                        docker images ${DOCKERHUB_REPO} --format "{{.ID}} {{.Repository}}:{{.Tag}} {{.CreatedAt}}"
                        
                        echo "Cleaning up old images..."
                        
                        REM Initialize counter
                        set COUNT=0
                        
                        REM Get all image IDs for our repository, sorted by creation date (newest first)
                        for /f "tokens=1" %%i in ('docker images ${DOCKERHUB_REPO} --format "{{.ID}}" ^| sort') do (
                            set /a COUNT+=1
                            if !COUNT! gtr 2 (
                                echo "Removing old image ID: %%i"
                                docker rmi -f %%i || echo "Could not remove image %%i, may be in use"
                            )
                        )
                        
                        echo "Cleanup completed"
                        endlocal
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully. Application is running at http://localhost:${HOST_PORT}"
            script {
                bat """
                    @echo off
                    echo "Currently running containers:"
                    docker ps
                """
            }
        }
        failure {
            echo "Pipeline failed. Check logs for details."
            script {
                bat """
                    @echo off
                    echo "Attempting to retrieve container logs..."
                    docker logs ${CONTAINER_NAME} || echo "No container logs available."
                    echo "Currently running containers:"
                    docker ps
                """
            }
        }
        always {
            archiveArtifacts artifacts: 'docker-compose.deploy.yml,.env,.env.deploy', allowEmptyArchive: true
            echo "Workspace preserved for debugging. Clean manually if needed."
        }
    }
}