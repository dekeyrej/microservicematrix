#Builder stage
FROM python:slim AS builder
ARG PANDAS
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements*.txt ./
RUN pip install -r requirements.txt
RUN if [ "$PANDAS" = "True" ] ; then pip install -r requirements-pandas.txt ; fi
#Operational stage
FROM python:slim
ARG MICROSERVICE
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PROD=2 \
    PYTHONUNBUFFERED=1 \
    SECRETS_PATH="None"
WORKDIR /code
COPY $MICROSERVICE.py .
EXPOSE 10255
ENV APP=$MICROSERVICE.py
CMD ["sh", "-c", "python /code/${APP}"]