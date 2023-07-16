# microservicematrix
Microservices Implementation of the matrix server

'Strangling' the kubematrix code base - 
-- Peeling off each of the 'servers'
-- making modifications as required to run standalone
-- creating a copy of the Dockerfile for each
-- testing, and when successful
-- commenting it out of the kubematrix monolith

docker run --env=PROD=0 --env=PATH=/opt/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin --env=PYTHONUNBUFFERED=1 --env=MSSERVERTYPE=MLB --workdir=/code -d 192.168.86.49:32000/mlb:registry