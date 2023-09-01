#!/bin/bash
for i in `cat builds.txt`
do
    if [ $i = 'aqi' ]; then pandas=True; else pandas=False; fi 
    buildctl build --frontend dockerfile.v0 --local context=. --local dockerfile=. --opt build-arg:MICROSERVICE=${i} --opt build-arg:PANDAS=${pandas} --output type=image,name=${repository}/${i}:${tag},registry.insecure=true,push=true
done