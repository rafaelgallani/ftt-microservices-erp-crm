import uuid
import sys
import os
import json

from nameko.rpc import rpc
from nameko.messaging import Publisher, consume
from nameko_redis import Redis

from logging import getLogger

from kombu import Exchange, Queue, Connection
from pricing_service import PricingService, ParsingError

from nameko.dependency_providers import Config

log = getLogger(__name__)

DEFAULT_PRODUCTS = (0, 1, 2, 123, 100, 200, 300)
DEFAULT_CUSTOMERS = (0, 1, 2, 123, 100, 200, 300)
DEFAULT_DELIVERY_TYPES = (0, 1, 2)

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

log.info('Received variables:')

log.info('RABBIT_USER     => {}'.format(os.getenv('RABBIT_USER', 'guest')))
log.info('RABBIT_PASSWORD => {}'.format(os.getenv('RABBIT_PASSWORD', 'guest')))
log.info('RABBIT_HOST     => {}'.format(os.getenv('RABBIT_HOST', 'rabbitmq')))
log.info('RABBIT_PORT     => {}'.format(os.getenv('RABBIT_PORT', '5672')))

log.info('MESSAGE_BUS_NAME => {}'.format(os.getenv('MESSAGE_BUS_NAME', 'erp_message_bus')))
log.info('FIRED_EVENT_ROUTING_KEY => {}'.format(os.getenv('FIRED_EVENT_ROUTING_KEY', 'createdOrderEvent')))

log.info('All OK.')

class QuoteService:
    name = "quote_service"
    log.info("@ Service")
    redis = Redis('development')
    log.info("@ Redis")

    @rpc
    def get(self, quote_id):
        log.info("@ GET - Quote")
        self.setup_default_data()
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
        log.info("@ POST - Quote")
        self.setup_default_data()
        quote_id = uuid.uuid4().hex

        quote_as_dict = json.loads(quote_json)
        quote_as_dict['id'] = quote_id

        self.handle_quote_data(quote_as_dict)

        quote_as_dict['items'] = json.dumps(quote_as_dict['items'])
        quote_as_dict['status'] = 'Pending'
        
        quote_as_dict['type'] = RECORD_TYPE
        
        self.redis.hmset(quote_id, quote_as_dict)

        quote_as_dict.pop('type')

        created_order_message = target_exchange.Message(quote_as_dict)

        quote_as_dict['items'] = json.loads(quote_as_dict['items'])
        producer.publish(quote_as_dict, routing_key=order_routing_key)

        return quote_id

    def setup_default_data(self):
        log.info("@ setup_default_data")
        self.create_default_products()
        self.create_default_customers()
        self.create_default_delivery_types()

    def create_default_products(self):
        log.info("@ create_default_products")
        for product in DEFAULT_PRODUCTS:
            product_id = str(product)
            record_id = 'product_'+product_id
            
            if not self.redis.hgetall(record_id):
                self.redis.hmset(record_id, {
                    "productId": product_id,
                    "price": 100
                })

    def create_default_customers(self):
        log.info("@ create_default_customers")
        for customer in DEFAULT_CUSTOMERS:
            customer_id = str(customer)
            record_id = 'customer_'+customer_id
            
            if not self.redis.hgetall(record_id):
                self.redis.hmset(record_id, {
                    "customerId": customer_id,
                })
    
    def create_default_delivery_types(self):
        log.info("@ create_default_delivery_types")
        for delivery_type in DEFAULT_DELIVERY_TYPES:
            delivery_type_id = str(delivery_type)
            record_id = 'delivery_type_'+delivery_type_id
            
            if not self.redis.hgetall(record_id):
                self.redis.hmset(record_id, {
                    "deliveryTypeId": delivery_type_id,
                })

    def handle_quote_data(self, quote_data):
        log.info("@ handle_quote_data")
        self.parse_products(quote_data['items'])
        self.parse_customer(quote_data)
        self.parse_delivery_type(quote_data)
    
    def parse_customer(self, quote_data):
        log.info("@ parse_customer")
        customer_id = str(quote_data['customerId'])
        if not self.redis.hgetall('customer_' + customer_id):
            raise ParsingError('Invalid customer id specified: "{customer_id}".'.format(customer_id=customer_id))
    
    def parse_delivery_type(self, quote_data):
        log.info("@ parse_delivery_type")
        delivery_type_id = str(quote_data['deliveryTypeId'])
        if not self.redis.hgetall('delivery_type_' + delivery_type_id):
            raise ParsingError('Invalid delivery type id specified: "{delivery_type_id}".'.format(delivery_type_id=delivery_type_id))
        
    def parse_products(self, items):
        log.info("@ parse_products")
        for index, item in enumerate(items):
            product_id_str = str(item['productId'])
            if not self.redis.hgetall('product_'+product_id_str):
                raise ParsingError('Invalid product id specified on item at {index}: "{invalid_product}".'.format(index=index, invalid_product=item['productId']))
    
    @rpc
    def get_all(self):
        log.info("@ GET ALL - Quote")
        records = []
        for key in self.redis.keys():
            log.info("@ LOGGING RECORDS...")
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