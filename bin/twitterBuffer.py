#!/usr/bin/env python

import config
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from app import app

# Run the server.

#app.run(host='0.0.0.0', port=8080, debug=True)
app.debug = True
server = pywsgi.WSGIServer(('', config.API_PORT), app, handler_class=WebSocketHandler)
server.serve_forever()
