# Import flask and template operators
from flask import Flask, render_template

# Import SQLAlchemy
from flask.ext.sqlalchemy import SQLAlchemy

# Define the WSGI application object
app = Flask(__name__)

# Configurations
app.config.from_object('config')

# Define the database object which is imported
# by modules and controllers
db = SQLAlchemy(app)

# HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

# Import modules using blueprints
from app.stream.controllers import stream_module
#from app.list.controllers import list_module
#from app.user.controllers import user_module
#from app.tweet.controllers import tweet_module

# Register blueprints
app.register_blueprint(stream_module)
#app.register_blueprint(list_module)
#app.register_blueprint(user_module)
#app.register_blueprint(tweet_module)

# Build the database:
# This will create the database file using SQLAlchemy
db.create_all()
