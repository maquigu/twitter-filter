# Statement for enabling the development environment
DEBUG = True

# Define the application directory
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  

# Define the database - we are working with
# SQLite for this example
#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
SQLALCHEMY_DATABASE_URI = 'mysql://root:openfilter@localhost/twitter_buffer'

DATABASE_CONNECT_OPTIONS = {}

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED     = True

# Use a secure, unique and absolutely secret key for
# signing the data. 
CSRF_SESSION_KEY = "secret"

# Secret key for signing cookies
SECRET_KEY = "secret"

# Twitter creds
TWITTER_ACCESS_KEY = "2415405402-EYHCzrtpiUq5f1tPIHFnlLGOrv7Oq3ShLZrfoFy"
TWITTER_ACCESS_SECRET = "1n3I7j2ByQUX6htva7ukdG8wRp0gVKUQ0ytQzEWxmi1XF"
TWITTER_CONSUMER_KEY = "AuP5g6beIccHYo1hPnJWrPIRM"
TWITTER_CONSUMER_SECRET = "4Yub0TfCNH1AlzscmRMpxUujfckT4dN8e5sV3iSxHEBtRjjbgd"

# Celery params
CELERY_QUEUE = "twitter_buffer"
CELERY_AMQP_BROKER = "amqp://guest:guest@localhost:5672"

# API location (for client)

API_HOST = "localhost"
API_PORT = 8080
