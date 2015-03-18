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
    Stream,
    User,
    Tweet,
    Hashtag,
    Mention,
    Share,
    Base
)

app = Flask(__name__)
app.config.from_object('config')

celery = Celery(config.CELERY_CATCHER_QUEUE, broker=config.CELERY_AMQP_BROKER)
celery.conf.CELERY_RESULT_BACKEND = config.CELERY_RESULT_BACKEND
auth = OAuth(config.TWITTER_ACCESS_KEY, config.TWITTER_ACCESS_SECRET, config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
twitter_stream = TwitterStream(auth = auth)
db = SQLAlchemy(app)
db.Model = Base

@celery.task
def catch_stream(stream_name):
    follow = []
    stream_obj = db.session.query(Stream).filter(Stream.name==stream_name).first()
    for lot_obj in stream_obj.lots:
        for user_obj in lot_obj.users:
            follow.append(user_obj.tw_id)
    try:
        sys.stderr.write('Stream catcher following: ' + repr(follow) + '\n')
        follow_csv = ','.join(follow)
        for message in twitter_stream.statuses.filter(follow=follow_csv, track=follow_csv):
            sys.stderr.write(pformat(message)+'\n') 
    except Exception, e:
        sys.stderr.write(repr(e)+'\n')
