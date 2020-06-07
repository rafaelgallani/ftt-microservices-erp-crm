import json

from nameko.rpc import RpcProxy
from nameko.web.handlers import http
from werkzeug.wrappers import Response

from pricing_service import PricingService

class GatewayService:
    name = 'gateway'

    orders_rpc, quotes_rpc = RpcProxy('order_service'), RpcProxy('quote_service')

    @http('GET', '/quote/<string:quote_id>')
    def get_quote(self, request, quote_id):
        quote = self.quotes_rpc.get(quote_id)

        return Response(
            json.dumps(quote, default=lambda x: x.__dict__),
            mimetype='application/json',
            status=200
        )

    @http('POST', '/quote')
    def post_quote(self, request):
        data = PricingService(json.loads(request.get_data(as_text=True)))
        quote_json = json.dumps(data, default=lambda x: x.__dict__)

        quote_id = self.quotes_rpc.create(quote_json)
        data.id = quote_id

        response = {
            "success": True,
            "data": data,
        }

        return Response(
            json.dumps(response, default=lambda x: x.__dict__),
            mimetype='application/json',
            status=201
        )