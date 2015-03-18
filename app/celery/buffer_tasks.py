import sys
import simplejson as json
from celery import Celery
import logging as log
import config
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from twitter import *
from pprint import pformat
from app.models import (
    User,
    Lot,
    Base
)

app = Flask(__name__)
app.config.from_object('config')

celery = Celery(config.CELERY_BUFFER_QUEUE, broker=config.CELERY_AMQP_BROKER)
celery.conf.CELERY_RESULT_BACKEND = config.CELERY_RESULT_BACKEND
auth = OAuth(config.TWITTER_ACCESS_KEY, config.TWITTER_ACCESS_SECRET, config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
twitter = Twitter(auth = auth)
db = SQLAlchemy(app)
db.Model = Base

@celery.task
def on_create_stream(stream_dict):
    if not isinstance(stream_dict, dict):
        raise Exception('stream_dict not a dict.')
    for l in stream_dict['lists']:
        lot_obj = db.session.query(Lot).filter(Lot.slug==l['slug']).first()
        if lot_obj is None:
            lot_obj = Lot(
                slug=l.get('slug'),
                name=l.get('name'),
                tw_id=l.get('twitter_id'),
                owner=Owner(screen_name=l.get('owner'))
            )
        results = twitter.lists.members(slug=l['slug'], owner_screen_name=l['owner'])   
        for u in results['users']:
            user_obj = db.session.query(User).filter(User.screen_name==u.get('screen_name')).first()
            if user_obj is None:
                user_obj = User(
                    screen_name=u['screen_name'],
                    tw_id=u['id_str'],
                    location=u['location'],
                    json_str=json.dumps(u)
                )
                lot_obj.users.append(user_obj) 
                sys.stderr.write('Adding:\n' + u['screen_name'] + '\n')
        db.session.add(lot_obj)
        db.session.commit()

