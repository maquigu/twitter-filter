import os
import config

# Import flask and template operators
from flask import render_template, send_from_directory, jsonify
# Import Bootstrap
from flask_bootstrap import Bootstrap
# Import Flask-sockets
from flask_sockets import Sockets
# DB Models
from app.models import app, db, log

# Set app root
app.root_path = os.path.abspath(os.path.dirname(__file__))
#app.config['SQLALCHEMY_ECHO'] = True #Enable to see raw SQL

# Bootstrap it
Bootstrap(app)
# Import mods using blueprints
from app.controllers.stream import stream_mod
from app.controllers.lot import lot_mod
from app.controllers.user import user_mod
from app.controllers.socket import socket_mod

# Setup Web Socket
sockets = Sockets(app)


# Register blueprints
app.register_blueprint(stream_mod)
app.register_blueprint(lot_mod)
app.register_blueprint(user_mod)
#app.register_blueprint(tweet_mod)
sockets.register_blueprint(socket_mod)
@app.route('/')
def default():
	return  jsonify(message='success')

# route favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


