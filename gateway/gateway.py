import os
import json

from nameko.standalone.rpc import ClusterRpcProxy
from nameko.exceptions import RemoteError
from nameko.web.handlers import http
from werkzeug.wrappers import Response

from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from pricing_service import PricingService
from pricing_service import ParsingError
from flask_swagger_ui import get_swaggerui_blueprint

from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)

amqp_uri = 'amqp://{RABBIT_USER}:{RABBIT_PASSWORD}@{RABBIT_HOST}:{RABBIT_PORT}/'.format(
    RABBIT_USER=os.getenv('RABBIT_USER', 'guest'),
    RABBIT_PASSWORD=os.getenv('RABBIT_PASSWORD', 'guest'),
    RABBIT_HOST=os.getenv('RABBIT_HOST', 'rabbitmq'),
    RABBIT_PORT=os.getenv('RABBIT_PORT', '5672'),
)

CONFIG = {'AMQP_URI': amqp_uri}

@app.errorhandler(403)
def unauthorized():
    return jsonify({"statusCode": 403, "description": "Unauthorized."}), 403

@app.errorhandler(404)
def not_found(a):
    return jsonify({"statusCode": 404, "description": "Resource not found."}), 404

@app.errorhandler(405)
def not_allowed(*args):
    return jsonify({"statusCode": 405, "description": "Invalid method."}), 405

@app.route('/api/crm/quote/', methods=['POST', 'GET'])
def generate_quote():
    app.logger.info('Calling {} on path {}'.format(request.method, '/api/crm/quote/'))
    try:
        app.logger.info('Logging with cluster')
        with ClusterRpcProxy(CONFIG) as rpc:
            app.logger.info('Cluster passed:')
            if request.method == 'POST':
                app.logger.info('Create:')
                quote_data = json.loads(request.get_data(as_text=True))

                data = PricingService(quote_data)
                quote_json = json.dumps(data, default=lambda x: x.__dict__)

                quote_id = rpc.quote_service.create(quote_json)
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
            else:
                app.logger.info('Get all:')
                quotes = rpc.quote_service.get_all()
                return Response(
                    json.dumps(quotes, default=lambda x: x.__dict__),
                    mimetype='application/json',
                    status=200
                )
    except ParsingError as e:
        return Response(
            json.dumps({
                "error": "Parsing error occurred: {}".format(str(e))
            }, default=lambda x: x.__dict__),
            mimetype='application/json',
            status=500
        )    
    except RemoteError as e:
        return Response(
            json.dumps({
                "error": "Parsing error occurred: {}".format(str(e.value))
            }, default=lambda x: x.__dict__),
            mimetype='application/json',
            status=500
        )    
    except Exception as e:
        return Response(
            json.dumps({
                "error": "Unexpected exception occurred: {}".format(str(e))
            }, default=lambda x: x.__dict__),
            mimetype='application/json',
            status=500
        )    

@app.route('/api/crm/quote/<string:quote_id>', methods=['GET'])
def get_quote(quote_id):
    app.logger.info('Calling {} on path {}'.format(request.method, '/api/crm/quote/<string:quote_id>'))
    try:
        app.logger.info('Logging with cluster')
        with ClusterRpcProxy(CONFIG) as rpc: 
            app.logger.info('Cluster passed:')
            quote = rpc.quote_service.get(quote_id)
            if quote:
                return Response(
                    json.dumps(quote, default=lambda x: x.__dict__),
                    mimetype='application/json',
                    status=201
                )
            else:
                return Response(
                    json.dumps({
                        "error": 'Id {} not found.'.format(quote_id),
                    }, default=lambda x: x.__dict__),
                    mimetype='application/json',
                    status=404
                )
    except Exception as e:
        return Response(
            json.dumps({
                "error": "Unexpected exception occurred: {}".format(str(e))
            }, default=lambda x: x.__dict__),
            mimetype='application/json',
            status=500
        )

@app.route('/api/crm/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

SWAGGER_URL = '/api/crm/swagger'
API_URL = '/api/crm/static/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
       
@app.route('/api/crm/', methods=['GET'])
def get_home():
    return redirect('/api/crm/swagger', code=308)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)