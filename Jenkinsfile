pipeline {
    agent { label 'main-executor' }

    environment {
        LOCAL_REGISTRY = 'localhost:5000'
        DOCKERHUB_REPO = "${LOCAL_REGISTRY}/africanapi"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        CONTAINER_NAME = 'african-capitals-api'
        HOST_PORT = '8000'
        CONTAINER_PORT = '8000'
        TRIVY_IMAGE = 'aquasec/trivy:0.51.1'
        TRIVY_LOCAL_IMAGE = "${LOCAL_REGISTRY}/aquasec/trivy:0.51.1"
        REDIS_IMAGE = 'redis:alpine'
        REDIS_LOCAL_IMAGE = "${LOCAL_REGISTRY}/redis:alpine"
        REGISTRY_IMAGE = 'registry:2'
        REGISTRY_LOCAL_IMAGE = "${LOCAL_REGISTRY}/registry:2"
        TRIVY_SEVERITY = ''//'HIGH,CRITICAL'
    }

    stages {
        stage('Start Local Registry') {
            steps {
                script {
                    bat """
                        @echo off
                        echo "Starting local registry..."
                        docker-compose up -d registry
                        
                        echo "Waiting for registry to be ready..."
                        setlocal EnableDelayedExpansion
                        set MAX_ATTEMPTS=30
                        set ATTEMPT=0
                        :CHECK_REGISTRY
                        curl -f -s http://localhost:5000/v2/ >nul
                        if %ERRORLEVEL% equ 0 (
                            echo "Registry is ready"
                            goto :END
                        )
                        set /a ATTEMPT+=1
                        if !ATTEMPT! lss %MAX_ATTEMPTS% (
                            echo "Registry not yet healthy. Retrying in 1 second (attempt !ATTEMPT! of %MAX_ATTEMPTS%)..."
                            echo "Registry logs for debugging:"
                            docker logs africanapi_python_flask_cicd-registry-1
                            timeout /t 1 /nobreak
                            goto :CHECK_REGISTRY
                        )
                        echo "Registry failed to become healthy after %MAX_ATTEMPTS% attempts."
                        echo "Final registry logs:"
                        docker logs africanapi_python_flask_cicd-registry-1
                        exit /b 1
                        :END
                        endlocal
                    """
                }
            }
        }

        stage('Prepare Images') {
            steps {
                script {
                    def pullAndPushImage = { String dockerHubImage, String localImage ->
                        def maxRetries = 3
                        def retryDelay = 5

                        bat """
                            @echo off
                            echo "Checking registry availability..."
                            
                            set RETRY_COUNT=0
                            :CHECK_REGISTRY
                            curl -f -s localhost:5000/v2/_catalog
                            if %ERRORLEVEL% neq 0 (
                                set /a RETRY_COUNT+=1
                                if %RETRY_COUNT% leq ${maxRetries} (
                                    echo "Registry not yet available. Retrying in ${retryDelay} seconds (attempt %RETRY_COUNT% of ${maxRetries})..."
                                    timeout /t ${retryDelay} /nobreak
                                    goto CHECK_REGISTRY
                                ) else (
                                    echo "Failed to connect to registry after ${maxRetries} attempts. Exiting."
                                    exit 1
                                )
                            )

                            echo "Checking if image ${localImage} exists..."
                            docker pull ${localImage} 2>nul
                            if %ERRORLEVEL% neq 0 (
                                echo "Image ${localImage} not found in local registry. Pulling from Docker Hub..."
                                docker pull ${dockerHubImage}
                                if %ERRORLEVEL% neq 0 (
                                    echo "Failed to pull ${dockerHubImage} from Docker Hub. Exiting."
                                    exit 1
                                )
                                echo "Pushing image to local registry as ${localImage}..."
                                docker tag ${dockerHubImage} ${localImage}
                                docker push ${localImage}
                                if %ERRORLEVEL% neq 0 (
                                    echo "Failed to push ${localImage} to local registry. Exiting."
                                    exit 1
                                )
                            ) else (
                                echo "Image ${localImage} found in local registry."
                            )
                        """
                    }

                    pullAndPushImage(env.TRIVY_IMAGE, env.TRIVY_LOCAL_IMAGE)
                    pullAndPushImage(env.REDIS_IMAGE, env.REDIS_LOCAL_IMAGE)
                    pullAndPushImage(env.REGISTRY_IMAGE, env.REGISTRY_LOCAL_IMAGE)
                }
            }
        }

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
                            docker build --no-cache -t ${DOCKERHUB_REPO}:${IMAGE_TAG} .
                        """
                    }
                }
            }
        }

        stage('Push to Local Registry') {
            steps {
                script {
                    retry(3) {
                        bat """
                            docker push ${DOCKERHUB_REPO}:${IMAGE_TAG}
                        """
                    }
                }
            }
        }

        stage('Verify Image Push') {
            steps {
                script {
                    bat """
                        @echo off
                        echo "Verifying image push to local registry..."
                        docker inspect ${DOCKERHUB_REPO}:${IMAGE_TAG}
                        if %ERRORLEVEL% neq 0 (
                            echo "Image verification failed. Image may not have been pushed correctly."
                            exit 1
                        ) else (
                            echo "Image successfully pushed and verified in local registry."
                        )
                    """
                }
            }
        }

        stage('Trivy Scan') {
            steps {
                script {
                    def trivyCacheDir = "${WORKSPACE}/.trivycache"

                    bat """
                        @echo off
                        echo "Running Trivy scan..."

                        if not exist "${trivyCacheDir}" mkdir "${trivyCacheDir}"

                        docker run --rm ^
                            -v /var/run/docker.sock:/var/run/docker.sock ^
                            -v "${trivyCacheDir}:/root/.cache/" ^
                            -v "%CD%:/scan" ^
                            ${TRIVY_LOCAL_IMAGE} image ^
                            --security-checks vuln,config ^
                            --severity %TRIVY_SEVERITY% ^
                            --format json ^
                            --output /scan/trivy-report.json ^
                            ${DOCKERHUB_REPO}:${IMAGE_TAG}

                        echo "Trivy scan completed. Check trivy-report.json for details."
                    """

                    archiveArtifacts artifacts: 'trivy-report.json', allowEmptyArchive: true

                    script {
                        def trivyReport = readJSON file: 'trivy-report.json'
                        def hasVulnerabilities = trivyReport.Results.any { result ->
                            result.Vulnerabilities != null && !result.Vulnerabilities.isEmpty()
                        }

                        if (hasVulnerabilities) {
                            error "Trivy scan found vulnerabilities with severity ${TRIVY_SEVERITY}. See trivy-report.json for details."
                        } else {
                            echo "No vulnerabilities found with severity ${TRIVY_SEVERITY}."
                        }
                    }
                }
            }
        }

        stage('Trivy Filesystem Scan') {
            steps {
                script {
                    def trivyCacheDir = "${WORKSPACE}/.trivycache"
                    bat """
                        @echo off
                        echo "Running Trivy filesystem scan..."
                        if not exist "${trivyCacheDir}" mkdir "${trivyCacheDir}"
                        docker run --rm -v "${trivyCacheDir}:/root/.cache/" -v "%CD%:/scan" ${TRIVY_LOCAL_IMAGE} fs --security-checks vuln,config --severity %TRIVY_SEVERITY% --format json --output /scan/trivy-fs-report.json /scan
                    """
                    archiveArtifacts artifacts: 'trivy-fs-report.json', allowEmptyArchive: true
                }
            }
        }

        stage('Prepare Docker Compose Environment') {
            steps {
                script {
                    bat """
                        @echo off
                        echo IMAGE_TAG=${IMAGE_TAG} > .env.deploy
                        echo DOCKERHUB_REPO=${DOCKERHUB_REPO} >> .env.deploy
                    """
                    
                    def hostTimezone = bat(script: 'powershell -Command "[System.TimeZoneInfo]::Local.Id"', returnStdout: true).trim()
                    def ianaTimezone = "Etc/UTC"
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
                            echo       - ./app/static:/app/app/static
                            echo       - ./app/cache:/app/app/cache
                            echo       - /etc/localtime:/etc/localtime:ro
                            echo     healthcheck:
                            echo       test: ["CMD", "curl", "-s", "-f", "http://localhost:${CONTAINER_PORT}/api/v1/health"]
                            echo       interval: 30s
                            echo       timeout: 10s
                            echo       retries: 3
                            echo       start_period: 5s
                            echo     restart: unless-stopped
                            echo     depends_on:
                            echo       redis:
                            echo         condition: service_healthy
                            echo   redis:
                            echo     image: ${REDIS_LOCAL_IMAGE}
                            echo     ports:
                            echo       - "6379:6379"
                            echo     volumes:
                            echo       - redis_data:/data
                            echo     healthcheck:
                            echo       test: ["CMD", "redis-cli", "ping"]
                            echo       interval: 10s
                            echo       timeout: 3s
                            echo       retries: 3
                            echo       start_period: 5s
                            echo     restart: unless-stopped
                            echo volumes:
                            echo   redis_data:
                        ) > docker-compose.deploy.yml
                    """
                }
            }
        }

        stage('Deploy with Docker Compose') {
            steps {
                script {
                    bat """
                        @echo off
                        echo "Stopping any existing containers..."
                        docker-compose -f docker-compose.deploy.yml down || echo "No docker-compose services to stop"

                        echo "Starting new containers..."
                        docker-compose -f docker-compose.deploy.yml up -d

                        echo "Container status:"
                        docker ps
                    """
                }
            }
        }

        stage('Run Tests') {
            steps {
                bat """
                    cd app
                    set PYTHONPATH=/app
                    python -m unittest discover -s tests
                """
            }
        }

        stage('Cleanup Old Images') {
            steps {
                script {
                    bat """
                        @echo off
                        echo "Cleaning up old images..."
                        docker image prune -a -f
                        echo "Cleanup completed"
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
                    echo "Stopping and removing registry container..."
                    docker-compose -f docker-compose.yml down || echo "No docker-compose services to stop."
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