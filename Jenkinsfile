pipeline {
    agent any

    environment {
        // Core application metadata
        APP_NAME         = 'flask-app'
        DOCKER_REGISTRY  = 'dhinesh2605' // Change to your registry
        IMAGE_TAG        = "${env.BUILD_NUMBER}"
        IMAGE_NAME       = "${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}"
        
        // Remote Minikube Server Details
        REMOTE_SSH_USER  = 'ubuntu'                        // Change to your remote user
        REMOTE_SSH_HOST  = '3.111.144.185'                  // Change to your remote Minikube server IP
        
        // Jenkins Credentials IDs
        DOCKER_CREDS_ID  = 'docker-hub-credentials'        // Configured in Jenkins
        SSH_KEY_CREDS_ID = 'minikube-ssh-key'              // Configured in Jenkins
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh 'pip3 install --break-system-packages -r app/requirements.txt'
            }
        }

        stage('Test') {
            steps {
                sh 'python3 -m py_compile app/app.py'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker image: ${IMAGE_NAME}"
                sh "docker build -t ${IMAGE_NAME} -t ${DOCKER_REGISTRY}/${APP_NAME}:latest app/"
            }
        }

        stage('Docker Image Scan') {
            steps {
                echo "Scanning container image with Trivy..."
                // Scans the built container image before pushing it to the registry
                sh "trivy image --severity HIGH,CRITICAL --exit-code 0 ${IMAGE_NAME}"
            }
        }

        stage('Push Image to Registry') {
            steps {
                withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDS_ID}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    echo "Logging into Docker Hub and pushing image..."
                    sh "echo ${DOCKER_PASS} | docker login -u ${DOCKER_USER} --password-stdin"
                    sh "docker push ${IMAGE_NAME}"
                }
            }
        }

        stage('Copy K8s Fikes') {
            steps {
                // Securely injects the private key into the SSH authentication agent
                sshagent(credentials: ["${SSH_KEY_CREDS_ID}"]) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${REMOTE_SSH_USER}@${REMOTE_SSH_HOST} mkdir -p /tmp/k8s
                        scp -o StrictHostKeyChecking=no -r k8s/*  ${REMOTE_SSH_USER}@${REMOTE_SSH_HOST}:/tmp/k8s/
                    """
                }
            }
        }

        stage('Remote Deploy to Minikube') {
            steps {
                // Securely injects the private key into the SSH authentication agent
                sshagent(credentials: ["${SSH_KEY_CREDS_ID}"]) {
                    echo "Connecting to remote Minikube server at ${REMOTE_SSH_HOST}..."
                    
                    // 1. Ensure the remote server knows about the new image and template the manifests
                    // 2. Apply the manifest files via kubectl on the Minikube server
                    sh """
                        ssh -o StrictHostKeyChecking=no ${REMOTE_SSH_USER}@${REMOTE_SSH_HOST} '
                            echo "Updating Kubernetes deployment image to ${IMAGE_NAME}..."

                            kubectl get deployment flask-app -n icanio >/dev/null 2>&1

                            if [ \$? -ne 0 ]; then
                                echo "New deployment"
                                kubectl apply -f /tmp/k8s/
                            else
                                echo "Update in the deployment"
    
                                kubectl set image deployment/flask-app flask-app=${IMAGE_NAME} -n icanio
                            fi
                                
                            # Verify rolling restart status
                            kubectl rollout status deployment/${APP_NAME} -n icanio --timeout=60s
                        '
                    """
                }
            }
        }
        stage('Verification') {
            steps {
                // Securely injects the private key into the SSH authentication agent
                sshagent(credentials: ["${SSH_KEY_CREDS_ID}"]) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${REMOTE_SSH_USER}@${REMOTE_SSH_HOST} '
                        kubectl get pods -n icanio
                        kubectl get svc -n icanio
                        kubectl get deployment flask-app -n icanio
                    """
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline finished processing. Cleaning up local Docker footprint...'
            sh "docker rmi ${IMAGE_NAME} || true"
        }
        success {
            echo 'Flask application successfully verified, built, and deployed to Minikube!'
        }
        failure {
            echo 'Pipeline failed. Check stage logs for Trivy vulnerabilities or SSH connectivity errors.'
        }
    }
}
