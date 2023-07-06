cp c:\Users\Joe\Desktop\Python\wheels\*.whl .\wheels
docker build -f Dockerfile.garmin -t 192.168.86.49:32000/garmin:registry .
docker push 192.168.86.49:32000/garmin:registry
kubectl rollout restart -n default deployment garmin


# kubectl scale -n default deployment garmin --replicas=1
