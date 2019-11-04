import os

from flask import Flask, jsonify, redirect
from flask_socketio import SocketIO
from flask_redis import FlaskRedis
from flask_cors import CORS

socketio = SocketIO()
redis_store = FlaskRedis()


def create_app():
    app = Flask(__name__)

    origins = os.environ['ORIGINS'].split(', ')
    app.config['REDIS_URL'] = os.environ['REDISCLOUD_URL']

    CORS(app, resources={r'/api/*': {'origins': origins}})

    socketio.init_app(app, cors_allowed_origins=origins)
    redis_store.init_app(app, decode_responses=True)

    from .api import api
    from .socket import socket
    app.register_blueprint(api)
    app.register_blueprint(socket)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return redirect(os.environ['CLIENT_URL'])

    return app
