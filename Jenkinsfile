pipeline {
    environment {
        SKIP = 'false'
    }
    agent any
    stages {
        stage('Test') {
            agent {label 'python3'}
            steps {
                script {
                    if (env.GIT_PREVIOUS_SUCCESSFUL_COMMIT != null) {
                        if (GIT_PREVIOUS_SUCCESSFUL_COMMIT == GIT_COMMIT) {
                            SKIP = 'true'
                            echo "Will skip deployment"
                        } 
                    } else {
                        SKIP = 'true'
                        echo "Will skip deployment"
                    }
                    dir('.') {
                        sh 'chmod u+x build.sh'
                        sh 'bash -c ./build.sh'
                        stash(name: 'compiled-results', includes: '*.py*')
                    }
                }
            }
        }
        stage('Build') {
            agent {label 'docker'}
            environment {
                DOCKER_BUILDKIT=1
            }
            steps {
                script {
                    sh 'python3 build_images.py'
                }
            }
        }
        stage('Push and Deploy') {
            agent {label 'kubectl'}
            when { expression { SKIP != 'true' } }
            steps {
                echo 'Deploying'
                script {
                    sh 'python3 push_deploy_images.py'
                }
            }
        }
    }
}