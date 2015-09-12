#!/usr/bin/python

# import statements
from flask import Flask
from flask_sockets import Sockets
import json

# app setup

app = Flask(__name__)
sockets = Sockets(app)

# functions

@sockets.route('/echo')
def echo_socket(ws):
    while True:
        message = ws.receive()
	ws.send(message)

@sockets.route('/send_gesture')


@app.route('/')
def hello():
    return "Hello world! This is the landing page for ClaySpace."
