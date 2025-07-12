#!/usr/bin/env bash
export repository=ghcr.io/dekeyrej
export tag=dev
export BUILDX_BUILDER=container

for i in `cat utilities/builds.txt`
do
    docker buildx build --platform linux/amd64 --build-arg MICROSERVICE=${i} --tag ${repository}/${i}:${tag} --push .
done

# docker buildx build --platform linux/amd64,linux/arm64 --build-arg MICROSERVICE=${i} --tag ${repository}/${i}:${tag} --push .

# docker buildx build --build-arg MICROSERVICE=events --tag ghcr.io/dekeyrej/events:latest --push .
# BUILDX_BUILDER=container docker buildx build --platform linux/amd64,linux/arm64 --build-arg MICROSERVICE=events --tag ghcr.io/dekeyrej/events:latest --push .
# buildctl build --frontend dockerfile.v0 --local context=. --local dockerfile=. --opt build-arg:MICROSERVICE=${i} --output type=image,name=${repository}/${i}:${tag},registry.insecure=true,push=true