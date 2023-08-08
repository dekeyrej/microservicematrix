TAG=calendar
docker build -f Dockerfile.$TAG -t 192.168.86.49:32000/$TAG:registry .
docker push 192.168.86.49:32000/$TAG:registry
kubectl rollout restart -n default deployment $TAG


# kubectl scale -n default deployment $TAG --replicas=1


# 192.168.86.49:32000/kubeagent:registry