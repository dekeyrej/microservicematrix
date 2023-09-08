#!/bin/bash
for i in `cat builds.txt` 
do 
    kubectl rollout restart deployment ${i}
    sleep 5
done