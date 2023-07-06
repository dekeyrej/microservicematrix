cp c:\Users\Joe\Desktop\Python\wheels\*.whl .\wheels
docker build -f Dockerfile.github -t 192.168.86.49:32000/github:registry .
docker push 192.168.86.49:32000/github:registry
kubectl rollout restart -n default deployment github


# kubectl scale -n default deployment github --replicas=1
