# syntax=docker/dockerfile-upstream:master-labs

FROM python:3.11.4

ADD https://github.com/rosaldanha/esphomeBroker.git /app

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 8001/tcp

ENTRYPOINT ["python", "./broker.py"]
