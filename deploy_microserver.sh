TAG=calendar
# docker build -f Dockerfile.$TAG -t 192.168.86.49:32000/$TAG:registry .
# for all except aqi
docker build --build-arg=MICROSERVICE=$TAG --build-arg=PANDAS=False -t 192.168.86.49:32000/$TAG:registry .
# just for aqi
docker build --build-arg=MICROSERVICE=aqi --build-arg=PANDAS=True -t 192.168.86.49:32000/aqi:registry .
docker push 192.168.86.49:32000/$TAG:registry
kubectl scale -n default deployment $TAG --replicas=0
kubectl rollout restart -n default deployment $TAG
kubectl scale -n default deployment $TAG --replicas=1

# 192.168.86.49:32000/kubeagent:registry