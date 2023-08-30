ARG PANDAS=False
#Builder stage
FROM python:slim AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements*.txt ./
RUN pip install -r requirements.txt
RUN IF [[ "$PANDAS" = "True" ]] ;pip install -r requirements-pandas.txt 
#Operational stage
FROM python:slim
ARG MICROSERVICE
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PROD=1 \
    PYTHONUNBUFFERED=1 \
    SECRETS_PATH="None"
WORKDIR /code
COPY $MICROSERVICE.py .
EXPOSE 10255
CMD ["python", "$MICROSERVICE.py"]