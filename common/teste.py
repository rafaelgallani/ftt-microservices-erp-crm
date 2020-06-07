import json
from collections import namedtuple


def _json_object_hook(d): 
    return namedtuple('X', d.keys())(*d.values())

def parse_as_obj(data): 
    return json.loads(data, object_hook=_json_object_hook)

class PricingService:

    def __init__(self, json_dict):
        json_string = json.dumps(json_dict)
        instance = parse_as_obj(json_string)

        self.customerId = instance.customerId
        self.createdDate = instance.createdDate
        self.deliveryType = instance.deliveryType
        self.address = instance.address

        if hasattr(instance, 'items'):
            self.items = []
            for item in instance.items:
                self.items.append(Product(item))


class Product:
    def __init__(self, item):
        self.productId = item.productId
        self.price = 10
        self.quantity = item.quantity

    @property
    def is_valid(self):
        return self.quantity and self.price


a = PricingService({
	"customerId": 1115623, 
	"createdDate": "29-05-2020",
	"deliveryType": "CIF",
	"address": "Rua Belem, nº 53",
	"items": [{
        "productId": 123, 
        "quantity": 321
    }]
})

json.dumps(a, default=lambda x: x.__dict__)