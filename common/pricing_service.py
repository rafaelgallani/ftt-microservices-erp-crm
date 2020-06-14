import uuid
from datetime import date, datetime

import json
from collections import namedtuple

def _json_object_hook(d): 
    return namedtuple('X', d.keys())(*d.values())

def parse_as_obj(data): 
    return json.loads(data, object_hook=_json_object_hook)

class PricingService:

    def __init__(self, json_dict):
        self.parse_required(json_dict)
        json_string = json.dumps(json_dict)
        instance = parse_as_obj(json_string)

        self.customerId = instance.customerId
        self.createdDate = instance.createdDate
        self.deliveryTypeId = instance.deliveryTypeId
        self.address = instance.address
        
        self.id = None

        if hasattr(instance, 'items'):
            self.items = []
            for item in instance.items:
                self.items.append(Product(item))

    def parse_required(self, quote):
        if not 'customerId' in quote:
            raise ParsingError('Customer was not specified [customerId].')
        if not 'createdDate' in quote:
            raise ParsingError('Creation date was not specified [createdDate].')
        if not 'deliveryTypeId' in quote:
            raise ParsingError('Delivery Type was not specified [deliveryTypeId].')
        if not 'address' in quote:
            raise ParsingError('Address was not specified [address].')
        if not 'items' in quote:
            raise ParsingError('Items was not specified [items].')

        if 'items' in quote:
            if isinstance(quote['items'], list):
                for index, item in enumerate(quote['items']):
                    if not 'productId' in item:
                        raise ParsingError('Product was not specified in item on index {} [productId].'.format(index))
                    if not 'quantity' in item:
                        raise ParsingError('Quantity was not specified in item on index {} [quantity].'.format(index))
            else:
                raise ParsingError(r'Items are not in the correct format: [{"productId": 1, "quantity": 1}]')


    @property
    def is_valid(self):
        return len(self.items) and all([item.is_valid() for item in self.items])

class ParsingError(Exception):
    pass

class Product:
    def __init__(self, item):
        self.productId = item.productId
        self.price = 10
        self.quantity = item.quantity

    @property
    def is_valid(self):
        return self.quantity and self.price