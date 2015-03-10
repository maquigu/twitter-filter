from celery import Celery
import logging as log
import config
from app.models import *
from twitter import *

celery = Celery(config.CELERY_QUEUE, broker=config.CELERY_AMQP_BROKER)
celery.conf.CELERY_RESULT_BACKEND = "amqp"
auth = OAuth(config.TWITTER_ACCESS_KEY, config.TWITTER_ACCESS_SECRET, config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
twitter = Twitter(auth = auth)

@celery.task
def on_create_stream(stream_dict):
    if not isinstance(stream_dict, dict):
        raise Exception('stream_dict not a dict.')
    for l in stream_dict['lists']:
        results = twitter.lists.members(slug=l['slug'], owner_screen_name=l['owner'])   
        log.debug(repr(results))

