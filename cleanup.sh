#!/bin/sh
kubectl get replicasets -n default -o wide > repsets
awk -f script.awk repsets > emptyrepsets
for i in `cat emptyrepsets`
do 
    kubectl delete replicaset $i --namespace $namespace
done