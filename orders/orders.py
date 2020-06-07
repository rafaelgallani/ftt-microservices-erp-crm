import uuid
import sys

from nameko.rpc import rpc
from nameko_redis import Redis
from pricing_service import PricingService

class OrderService:
    name = "order_service"

    redis = Redis('development')

    @rpc
    def get(self, order_id):
        order = self.redis.hgetall(order_id)
        order['quantity'] = float(order['quantity'])
        order['price'] = float(order['price'])
        return order

    @rpc
    def create(self, product_id, quantity, delivery_date):
        pricing_instance = PricingService(product_id, quantity, delivery_date)
        order_id = uuid.uuid4().hex
        self.redis.hmset(order_id, {
            "order_id": product_id,
            "product_id": product_id,
            "quantity": quantity,
            "delivery_date": delivery_date,
            "price": pricing_instance.get_price()
        })
        return order_id
