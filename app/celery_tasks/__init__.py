import sys
import simplejson as json
from celery import Celery
import logging as log
import config
from app.models import User
from flask.ext.sqlalchemy import SQLAlchemy
from twitter import *
from pprint import pformat
from app.models import (
    User,
    Base
)

celery = Celery(config.CELERY_QUEUE, broker=config.CELERY_AMQP_BROKER)
celery.conf.CELERY_RESULT_BACKEND = "amqp"
auth = OAuth(config.TWITTER_ACCESS_KEY, config.TWITTER_ACCESS_SECRET, config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
twitter = Twitter(auth = auth)
db = SQLAlchemy()
db.Model = Base

@celery.task
def on_create_stream(stream_dict):
    if not isinstance(stream_dict, dict):
        raise Exception('stream_dict not a dict.')
    for l in stream_dict['lists']:
        results = twitter.lists.members(slug=l['slug'], owner_screen_name=l['owner'])   
        for u in results['users']:
            user_obj = User(
                screen_name=u['screen_name'],
                tw_id=u['id_str'],
                location=u['location'],
                json_str=json.dumps(u)
            )
            sys.stderr.write('Adding:\n' + pformat(u) + '\n')
            db.session.add(user_obj)
        db.session.commit()

