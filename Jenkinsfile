podTemplate(label: 'jenkins-agent', cloud: 'kubernetes', serviceAccount: 'jenkins-admin',
  containers: [
    containerTemplate(name: 'python3',  image: 'localhost:32000/python:latest',   alwaysPullImage: true, ttyEnabled: true, command: 'cat'),
    containerTemplate(name: 'buildkit', image: 'localhost:32000/buildkit:latest', alwaysPullImage: true, ttyEnabled: true, privileged: true),
  ],
  volumes: [
    secretVolume(mountPath: '/etc/.ssh', secretName: 'ssh-home')
  ],
  envVars: [
    envVar(key: 'tag', value: 'registry'),
    envVar(key: 'repository', value: '192.168.86.49:32000'),
    envVar(key: 'namespace', value: 'default'),
  ]
) {
    node('jenkins-agent') {
        stage('Prepare'){
            checkout scm
        }
        stage('Test') {
            container('python3') {
                dir('/home/jenkins/agent/workspace/MicroServiceMatrix') {
                    sh '''
                        echo $tag $repository $namespace
                        chmod a+x build.sh
                        chmod a+x deploy.sh
                        chmod a+x cleanup.sh
                        export PROD=2
                        python3 -m venv .
                        . bin/activate
                        pip install pylint pylint-venv pytest
                        pip install -r requirements.txt
                        pip install -r requirements-pandas.txt
                        python3 -m pylint --fail-under 9.0 *.py
                        git config --global --add safe.directory /home/jenkins/agent/workspace/MicroServiceMatrix
                        python3 determine_tags.py
                    '''
                    stash(name: 'builds', includes: 'builds.txt')
                    milestone(1)
                }
            }
        }
        stage('Build Image(s)') {
            container('buildkit') {
                dir('/home/jenkins/agent/workspace/MicroServiceMatrix') {
                    unstash(name: 'builds')
                    if (fileExists('builds.txt')) {
                        echo "File builds.txt found!"
                        sh '''
                            if [ `stat -c %s builds.txt` -gt 0 ] 
                            then 
                                for i in `cat builds.txt` 
                                do
                                    if [ $i = \'aqi\' ]; then pandas=True; else pandas=False; fi 
                                    buildctl build --frontend dockerfile.v0 --local context=. --local dockerfile=. --opt build-arg:MICROSERVICE=${i} --opt build-arg:PANDAS=${pandas} --output type=image,name=${repository}/${i}:${tag},registry.insecure=true,push=true
                                done 
                            fi
                        '''
                    }
                }
                milestone(2)
            }
        }
        stage('Deploy Image(s)') {
            container('python3') {
                sh '''
                    echo $tag $repository $namespace
                    export PWD=`pwd`
                    ${PWD}/deploy.sh
                '''
                milestone(3)
            }
        }
        stage('Cleanup ReplicaSets') {
            container('python3') {
                sh '''
                    echo $tag $repository $namespace
                    export PWD=`pwd`
                    ${PWD}/cleanup.sh
                '''
                milestone(4)
            }
        }
    }
}

properties([[
    $class: 'BuildDiscarderProperty',
    strategy: [
        $class: 'LogRotator',
        artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '10', numToKeepStr: '2']
    ]
]);
