cp c:\Users\Joe\Desktop\Python\wheels\*.whl .\wheels
docker build -f Dockerfile.jenkins -t 192.168.86.49:32000/jenkins:registry .
docker push 192.168.86.49:32000/jenkins:registry
kubectl rollout restart -n default deployment jenkins


# kubectl scale -n default deployment jenkins --replicas=1
