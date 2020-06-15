import uuid
import sys
import os
import json

from nameko.rpc import rpc
from nameko.messaging import Publisher, consume
from nameko_redis import Redis

from kombu import Exchange, Queue, Connection
from pricing_service import PricingService, ParsingError

from nameko.dependency_providers import Config

DEFAULT_PRODUCTS = (0, 1, 2, 123, 100, 200, 300)

amqp_uri = 'amqp://{RABBIT_USER}:{RABBIT_PASSWORD}@{RABBIT_HOST}:{RABBIT_PORT}/'.format(
    RABBIT_USER=os.getenv('RABBIT_USER', 'guest'),
    RABBIT_PASSWORD=os.getenv('RABBIT_PASSWORD', 'guest'),
    RABBIT_HOST=os.getenv('RABBIT_HOST', 'rabbitmq'),
    RABBIT_PORT=os.getenv('RABBIT_PORT', '5672'),
)
channel = Connection(amqp_uri)
target_exchange = Exchange(os.getenv('MESSAGE_BUS_NAME', 'erp_message_bus'), channel=channel)

producer = channel.Producer(serializer='json', exchange=target_exchange)
order_routing_key = os.getenv('FIRED_EVENT_ROUTING_KEY', 'createdOrderEvent')

RECORD_TYPE = 'quote'

class QuoteService:
    name = "quote_service"
    redis = Redis('development')
    config = Config()

    @rpc
    def get(self, quote_id):
        self.create_default_products()
        quote = self.redis.hgetall(quote_id)
        if 'id' not in quote:
            return None

        try:
            record_type = quote.pop('type')
        except KeyError as e:
            pass
            
        quote['items'] = json.loads(quote['items'])
        quote['customerId'] = int(quote['customerId'])
        quote['deliveryTypeId'] = int(quote['deliveryTypeId'])
        return quote

    @rpc
    def create(self, quote_json):
        self.create_default_products()
        quote_id = uuid.uuid4().hex

        quote_as_dict = json.loads(quote_json)
        quote_as_dict['id'] = quote_id

        self.parse_products(quote_as_dict['items'])

        quote_as_dict['items'] = json.dumps(quote_as_dict['items'])
        quote_as_dict['status'] = 'Pending'
        
        quote_as_dict['type'] = RECORD_TYPE
        
        self.redis.hmset(quote_id, quote_as_dict)

        quote_as_dict.pop('type')

        created_order_message = target_exchange.Message(quote_as_dict)

        quote_as_dict['items'] = json.loads(quote_as_dict['items'])
        producer.publish(quote_as_dict, routing_key=order_routing_key)

        return quote_id

    def create_default_products(self):
        for product in DEFAULT_PRODUCTS:
            product_id = str(product)
            record_id = 'product_'+product_id
            
            if not self.redis.hgetall(record_id):
                self.redis.hmset(record_id, {
                    "productId": product_id,
                    "price": 100
                })

    def parse_products(self, items):
        for index, item in enumerate(items):
            product_id_str = str(item['productId'])
            if not self.redis.hgetall('product_'+product_id_str):
                raise ParsingError('Invalid product specified in item at {index}: {invalid_product}.'.format(index=index, invalid_product= item['productId']))
    
    @rpc
    def get_all(self):
        records = []
        for key in self.redis.keys():
            record = self.redis.hgetall(key)

            if 'type' in record and record['type'] == RECORD_TYPE:
                try:
                    record['items'] = json.loads(record['items'])
                except KeyError as e:
                    pass

                try:
                    record.pop('type')
                except KeyError as e:
                    pass
                
                records.append(record)
                
        return records