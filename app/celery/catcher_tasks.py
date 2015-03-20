import sys
import traceback
from datetime import datetime
import simplejson as json
from celery import Celery
import logging as log
import config
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
from app import init_app_db

app, db = init_app_db(config.FLASK_CONFIG_MODULE)
celery = Celery(config.CELERY_CATCHER_QUEUE, broker=config.CELERY_AMQP_BROKER)
celery.conf.CELERY_RESULT_BACKEND = config.CELERY_RESULT_BACKEND
auth = OAuth(config.TWITTER_ACCESS_KEY, config.TWITTER_ACCESS_SECRET, config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
twitter_stream = TwitterStream(auth = auth)

def _process_tweet(tweet_dict):
    user_obj = db.session.query(User).filter(User.tw_id==tweet_dict.get('user', {}).get('id_str', None)).first()
    if user_obj is None:
        u = tweet_dict['user']
        user_obj = User(
            screen_name=u['screen_name'],
            tw_id=u['id_str'],
            location=u['location'],
            json_str=json.dumps(u)
        )
    tweet_obj = Tweet(
        tw_id = tweet_dict['id_str'],
        created_at = datetime.strptime(tweet_dict['created_at'], '%a %b %d %H:%M:%S +0000 %Y'),
        json_str = json.dumps(tweet_dict),
        user = user_obj
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
                media_url = media['media_url'],
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
    try:
        sys.stderr.write('Stream catcher following: ' + repr(follow) + '\n')
        follow_csv = ','.join(follow)
        for tweet in twitter_stream.statuses.filter(follow=follow_csv, track=follow_csv):
            sys.stderr.write('Incoming: '+tweet['id_str']+'\n') 
            _process_tweet(tweet)
    except Exception, e:
        sys.stderr.write(pformat(tweet)+'\n')
        sys.stderr.write(traceback.format_exc()+'\n')
