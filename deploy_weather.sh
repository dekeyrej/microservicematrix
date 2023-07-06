cp c:\Users\Joe\Desktop\Python\wheels\*.whl .\wheels
docker build -f Dockerfile.weather -t 192.168.86.49:32000/weather:registry .
docker push 192.168.86.49:32000/weather:registry
kubectl rollout restart -n default deployment weather


# kubectl scale -n default deployment weather --replicas=1
