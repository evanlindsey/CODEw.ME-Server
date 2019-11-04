import os
import uuid

from flask import Blueprint, request
from flask_socketio import join_room, emit, send
from jose import jwt

from . import socketio, redis_store
from .schema import Code, Keys, ClientID, ClientCode, ClientTheme, ClientDetails


socket = Blueprint('socket', __name__)
url_prefix = '/socket'

secret = os.environ['SECRET']
limit = os.environ['LIMIT']


def decode_token(token):
    try:
        token = jwt.decode(token, secret, algorithms=['HS256'])
        return token['token']
    except:
        print('INVALID TOKEN')
        return None


def validate_token(token, room, client):
    token = decode_token(token)
    if token is not None:
        valid_client = redis_store.hget(token, room)
        if valid_client != client:
            print('INVALID CLIENT ID')
            return False
        return True
    return False


@socketio.on('connect', namespace=url_prefix)
def on_connect():
    print(request.sid + ' connected')


@socketio.on('disconnect', namespace=url_prefix)
def on_disconnect():
    print(request.sid + ' disconnected')


@socketio.on('join', namespace=url_prefix)
def on_join(token, room, client):
    room = room.lower()
    new_client = True
    # if client id exists
    if client is not None:
        # validate token
        if not validate_token(token, room, client):
            return None
        # get prior code repo
        repo = redis_store.hget(client, 'repo')
        if repo is not None:
            new_client = False
    if new_client:
        client = request.sid
        # create code repo
        repo = uuid.uuid4().hex
        code_schema = Code()
        code = code_schema.dump({'js': '', 'html': '', 'css': ''})
        redis_store.hmset(repo, code)
        # add client room/repo keys
        keys_schema = Keys()
        keys = keys_schema.dump({'room': room, 'repo': repo})
        redis_store.hmset(client, keys)
        # add valid room client id to token map
        token = decode_token(token)
        valid_client = {room: client}
        redis_store.hmset(token, valid_client)
    # push id to room
    redis_store.sadd(room, client)
    # join socket room
    join_room(room)
    print(client + ' joined room: ' + room)
    return client


@socketio.on('add', namespace=url_prefix)
def on_add(room):
    room = room.lower()
    payloads = []
    # for all clients in room
    clients = redis_store.smembers(room)
    if (len(clients) <= int(limit)):
        for client in clients:
            # add code/theme to list
            repo = redis_store.hget(client, 'repo')
            code_schema = Code()
            code = code_schema.dump(redis_store.hgetall(repo))
            theme = redis_store.hget(client, 'theme')
            schema = ClientDetails()
            payload = schema.dump(
                {'id': client, 'code': code, 'theme': theme})
            payloads.append(payload)
    else:
        schema = ClientID()
        payload = schema.dump({'id': 'full'})
        payloads.append(payload)
    # broacast current clients/code to room
    emit('added', payloads, room=room)


@socketio.on('remove', namespace=url_prefix)
def on_remove(token, room, client):
    room = room.lower()
    # validate token
    if not validate_token(token, room, client):
        return None
    # remove client from room
    redis_store.srem(room, client)
    # broadcast socket change to room
    schema = ClientID()
    payload = schema.dump({'id': client})
    emit('removed', payload, room=room, include_self=False)
    print(client + ' left room: ' + room)


@socketio.on('code', namespace=url_prefix)
def on_code(token, room, client, code, lang):
    room = room.lower()
    # validate token
    if not validate_token(token, room, client):
        return None
    # update client repo code
    repo = redis_store.hget(client, 'repo')
    redis_store.hset(repo, lang, code)
    # send code to room (except client)
    schema = ClientCode()
    payload = schema.dump({'id': client, 'code': code, 'lang': lang})
    emit('coded', payload, room=room, include_self=False)


@socketio.on('theme', namespace=url_prefix)
def on_theme(token, room, client, theme):
    room = room.lower()
    # validate token
    if not validate_token(token, room, client):
        return None
    # save theme
    redis_store.hset(client, 'theme', theme)
    # send theme to room (except client)
    schema = ClientTheme()
    payload = schema.dump({'id': client, 'theme': theme})
    emit('themed', payload, room=room, include_self=False)
