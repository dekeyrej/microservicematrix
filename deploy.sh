for i in `cat builds.txt`
do
    docker push 192.168.86.49:32000/$i:registry
done

sleep 5

for i in `cat builds.txt`
do
    kubectl rollout restart -n default deployment $i
    sleep 2
done