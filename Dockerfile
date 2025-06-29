#Builder stage
FROM python:3.12-slim AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN . /opt/venv/bin/activate
RUN pip install -r requirements.txt
COPY utilities/check_and_append_cacert.py .
COPY utilities/ca.crt .
RUN python check_and_append_cacert.py
#Operational stage
FROM python:3.12-slim
ARG MICROSERVICE
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PROD=1 \
    PYTHONUNBUFFERED=1 
WORKDIR /code
COPY config.py .
COPY $MICROSERVICE.py .
EXPOSE 10255
ENV APP=$MICROSERVICE.py
CMD ["sh", "-c", "python /code/${APP}"]