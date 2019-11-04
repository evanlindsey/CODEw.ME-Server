import os
import uuid
from flask import Blueprint, jsonify, request
from jose import jwt

api = Blueprint('api', __name__, url_prefix='/api')

secret = os.environ['SECRET']


@api.route('/token')
def get_token():
    uid = uuid.uuid4().hex
    token = jwt.encode({'token': uid}, 'secret', algorithm='HS256')
    payload = {'token': token}
    return jsonify(payload)
