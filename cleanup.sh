#!/bin/bash
for i in `kubectl get replicasets -n default -o wide | awk -f script.awk`
do 
    kubectl delete replicaset $i --namespace $namespace
done