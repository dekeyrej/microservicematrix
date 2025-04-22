for i in `cat builds.txt`
do
    buildctl build --frontend dockerfile.v0 --local context=. --local dockerfile=. --opt build-arg:MICROSERVICE=${i} --output type=image,name=${repository}/${i}:${tag},registry.insecure=true,push=true
done