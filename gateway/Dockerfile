FROM python:3

RUN apt-get update && apt-get -y install netcat && apt-get clean
WORKDIR /app

COPY ./gateway/requirements.txt ./
COPY ./gateway/static/swagger.json ./static/swagger.json
COPY ./common/pricing_service.py ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./gateway/config.yml ./
COPY ./gateway/run.sh ./
COPY ./gateway/gateway.py ./

RUN chmod +x ./run.sh

CMD ["./run.sh"]