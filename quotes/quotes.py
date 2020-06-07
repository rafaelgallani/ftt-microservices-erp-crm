import uuid
import sys
import json

from nameko.rpc import rpc
from nameko.messaging import Publisher, consume
from nameko_redis import Redis

from kombu import Exchange, Queue, Connection
from pricing_service import PricingService

channel = Connection('amqp://guest:guest@rabbitmq:5672//')
target_exchange = Exchange('erp_message_bus', channel=channel)

producer = channel.Producer(serializer='json', exchange=target_exchange)
order_routing_key = 'createdOrderEvent'

class QuoteService:
    name = "quote_service"
    redis = Redis('development')

    @rpc
    def get(self, quote_id):
        quote = self.redis.hgetall(quote_id)
        if 'id' not in quote:
            return None
            
        quote['items'] = json.loads(quote['items'])
        quote['customerId'] = int(quote['customerId'])
        quote['deliveryTypeId'] = int(quote['deliveryTypeId'])
        return quote

    @rpc
    def create(self, quote_json):
        quote_id = uuid.uuid4().hex

        quote_as_dict = json.loads(quote_json)
        quote_as_dict['id'] = quote_id
        quote_as_dict['items'] = json.dumps(quote_as_dict['items'])
        
        self.redis.hmset(quote_id, quote_as_dict)

        created_order_message = target_exchange.Message(quote_as_dict)

        quote_as_dict['items'] = json.loads(quote_as_dict['items'])
        producer.publish(quote_as_dict, routing_key=order_routing_key)

        return quote_id