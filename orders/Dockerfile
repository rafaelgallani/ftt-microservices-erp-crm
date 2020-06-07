FROM python:3

RUN apt-get update && apt-get -y install netcat && apt-get clean
WORKDIR /app

COPY ./common/pricing_service.py ./
COPY ./orders/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./orders/config.yml ./
COPY ./orders/run.sh ./
COPY ./orders/orders.py ./

RUN chmod +x ./run.sh

CMD ["./run.sh"]
