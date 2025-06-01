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
                        echo "Stopping any existing containers..."
                        docker-compose -f docker-compose.deploy.yml down || echo "No existing containers to stop"
                        
                        echo "Starting new containers..."
                        docker-compose -f docker-compose.deploy.yml up -d
                        
                        echo "Container status:"
                        docker ps
                    """
                    
                    // Health check loop
                    bat """
                        @echo off
                        setlocal enabledelayedexpansion
                        
                        echo "Starting health check..."
                        set MAX_RETRIES=15
                        set RETRY_DELAY=5
                        set RETRY_COUNT=0

                        :healthcheck_retry
                        echo "Attempt %RETRY_COUNT%/%MAX_RETRIES%: Checking health endpoint..."
                        curl.exe --max-time 10 http://localhost:${HOST_PORT}/health
                        if %errorlevel%==0 (
                            echo "Health check passed!"
                            goto :end
                        )

                        set /a RETRY_COUNT+=1
                        if %RETRY_COUNT% geq %MAX_RETRIES% (
                            echo "Health check failed after %MAX_RETRIES% attempts"
                            echo "Container logs:"
                            docker logs ${CONTAINER_NAME}
                            exit /b 1
                        )

                        echo "Application not ready, retrying in %RETRY_DELAY% seconds..."
                        timeout /t %RETRY_DELAY% /nobreak >nul
                        goto :healthcheck_retry
                        
                        :end
                        echo "Deployment successful!"
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
                bat """
                    @echo off
                    echo "Attempting to retrieve container logs..."
                    docker logs ${CONTAINER_NAME} || echo "No container logs available."
                """
            }
        }
        always {
            // Archive the deployment files for reference
            archiveArtifacts artifacts: 'docker-compose.deploy.yml,.env,.env.deploy', allowEmptyArchive: true
            
            // Don't immediately clean workspace to allow for debugging
            echo "Workspace preserved for debugging. Clean manually if needed."
        }
    }
}