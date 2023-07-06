cp c:\Users\Joe\Desktop\Python\wheels\*.whl .\wheels
docker build -f Dockerfile.moon -t 192.168.86.49:32000/moon:registry .
docker push 192.168.86.49:32000/moon:registry
kubectl rollout restart -n default deployment moon


# kubectl scale -n default deployment moon --replicas=1
