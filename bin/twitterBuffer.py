#!/usr/bin/env python

import config
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from app import app

# Run the server.

#app.run(host='0.0.0.0', port=8080, debug=True)
server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
server.serve_forever()