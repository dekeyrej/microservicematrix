cp c:\Users\Joe\Desktop\Python\wheels\*.whl .\wheels
docker build -f Dockerfile.events -t 192.168.86.49:32000/events:registry .
docker push 192.168.86.49:32000/events:registry
kubectl rollout restart -n default deployment events


# kubectl scale -n default deployment events --replicas=1
