import sys
from datetime import datetime
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
    URL,
    Media,
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

def _process_tweet(tweet_dict):
    tweet_obj = Tweet(
        tweet_id = tweet_dict['id_str'],
        timestamp = datetime.strptime(tweet_dict['created_at'], '%a %b %d %H:%M:%S +0000 %Y'),
        json_str = json.dumps(tweet_dict)
    )
    for hashtag in tweet_dict['entities']['hashtags']:
        hashtag_obj = db.session.query(Hashtag).filter(Hashtag.text==hashtag['text']).first()
        if hashtag_obj is None:
            hashtag_obj = Hashtag(text=hashtag['text'])
        tweet_obj.hashtags.append(hashtag_obj)
    for mention in tweet_dict['entities']['user_mentions']:
        mention_obj = db.session.query(Mention).filter(Mention.screen_name==mention['screen_name']).first()
        if mention_obj is None:
            mention_obj = Mention(
                tw_id = mention['id_str'],
                screen_name = mention['screen_name'],
                name = mention['name']
            )
        tweet_obj.mentions.append(mention_obj)
    for url in tweet_dict['entities']['urls']:
        url_obj = db.session.query(URL).filter(URL.url==url['url']).first()
        if url_obj is None:
            url_obj = URL(
                url = url['url'],
                display_url = url['display_url'],
                expanded_url = url['expanded_url']
            )
        tweet_obj.urls.append(url_obj)
    for media in tweet_dict['entities'].get('media',[]): # media is not always present
        media_obj = db.session.query(Media).filter(Media.tw_id == media['id_str']).first()
        if media_obj is None:
            media_obj = Media(
                tw_id = media['id_str'],
                url = media['media_url'],
                display_url = media['display_url']
            )
        tweet_obj.media.append(media_obj)
    db.session.add(tweet_obj)
    db.session.commit()

@celery.task
def catch_stream(stream_name):
    follow = []
    stream_obj = db.session.query(Stream).filter(Stream.name==stream_name).first()
    if stream_obj is None:
        return None
    for lot_obj in stream_obj.lots:
        for user_obj in lot_obj.users:
            follow.append(user_obj.tw_id)
    #try:
    sys.stderr.write('Stream catcher following: ' + repr(follow) + '\n')
    follow_csv = ','.join(follow)
    for tweet in twitter_stream.statuses.filter(follow=follow_csv, track=follow_csv):
            sys.stderr.write('Incoming: '+tweet['id_str']+'\n') 
            _process_tweet(tweet)
    #except Exception, e:
    #    sys.stderr.write(repr(e)+'\n')
