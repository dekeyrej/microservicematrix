#!/bin/bash
namespace=default
for i in `kubectl get replicasets --namespace $namespace -o wide | awk -f script.awk`
do 
    kubectl delete replicaset $i --namespace $namespace
done
