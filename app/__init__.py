import os
# Import flask and template operators
from flask import Flask, render_template, send_from_directory

# Import Bootstrap
from flask_bootstrap import Bootstrap

# Import SQLAlchemy
from flask.ext.sqlalchemy import SQLAlchemy

# Define the WSGI application object
app = Flask(__name__)

# Bootstrap it
Bootstrap(app)

# Configurations
app.config.from_object('config')

# route favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Define the database object which is imported
# by mods and controllers
db = SQLAlchemy(app)

# HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

# Import mods using blueprints
from app.controllers.stream import stream_mod
#from app.list.controllers import list_mod
#from app.user.controllers import user_mod
#from app.tweet.controllers import tweet_mod

# Register blueprints
app.register_blueprint(stream_mod)
#app.register_blueprint(list_mod)
#app.register_blueprint(user_mod)
#app.register_blueprint(tweet_mod)

# Build the database:
# This will create the database file using SQLAlchemy
db.create_all()
