cp c:\Users\Joe\Desktop\Python\wheels\*.whl .\wheels
docker build -f Dockerfile.mlb -t 192.168.86.49:32000/mlb:registry .
docker push 192.168.86.49:32000/mlb:registry
kubectl rollout restart -n default deployment mlb


# kubectl scale -n default deployment mlb --replicas=1
