FROM python:3

RUN apt-get update && apt-get -y install netcat && apt-get clean
WORKDIR /app

COPY ./common/pricing_service.py ./
COPY ./quotes/static/swagger.json ./static/swagger.json
COPY ./quotes/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./quotes/run.sh ./
COPY ./quotes/quotes.py ./

RUN chmod +x ./run.sh

CMD ["./run.sh"]

