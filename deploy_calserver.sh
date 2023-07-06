cp c:\Users\Joe\Desktop\Python\wheels\*.whl .\wheels
docker build -f Dockerfile.calendar -t 192.168.86.49:32000/calendar:registry .
docker push 192.168.86.49:32000/calendar:registry
kubectl rollout restart -n default deployment calendar


# kubectl scale -n default deployment calendar --replicas=1
