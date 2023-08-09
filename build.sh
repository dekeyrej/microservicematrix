for i in `cat builds.txt`
do
    docker build -f Dockerfile.$i -t 192.168.86.49:32000/$i:registry .
done