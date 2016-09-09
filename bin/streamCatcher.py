#!/usr/bin/env python
# encoding: utf-8

import socket
import sys
import os
import time
import traceback
from datetime import datetime
import simplejson as json
import logging as log
import config
from twitter import *
from twitter.util import printNicely
from twitter.stream import TwitterStream, Timeout, HeartbeatTimeout, Hangup
from pprint import pformat
from app.models import (
    Stream,
    User,
    Tweet,
    Hashtag,
    Mention,
    URL,
    Media,
    db,
    app
)

stream_timeout = 90 
auth = OAuth(config.TWITTER_ACCESS_KEY, config.TWITTER_ACCESS_SECRET, config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
rollback_ctr = 0

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
    insert(user_obj)
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
        insert(hashtag_obj)
        tweet_obj.hashtags.append(hashtag_obj)
    for mention in tweet_dict['entities']['user_mentions']:
        mention_obj = db.session.query(Mention).filter(Mention.screen_name==mention['screen_name']).first()
        if mention_obj is None:
            mention_obj = Mention(
                tw_id = mention['id_str'],
                screen_name = mention['screen_name'],
                name = mention['name']
            )
        insert(mention_obj)
        tweet_obj.mentions.append(mention_obj)
    for url in tweet_dict['entities']['urls']:
        url_obj = db.session.query(URL).filter(URL.url==url['url']).first()
        if url_obj is None:
            url_obj = URL(
                url = url['url'],
                display_url = url['display_url'],
                expanded_url = url['expanded_url']
            )
        insert(url_obj)
        tweet_obj.urls.append(url_obj)
    for media in tweet_dict['entities'].get('media',[]): # media is not always present
        media_obj = db.session.query(Media).filter(Media.tw_id == media['id_str']).first()
        if media_obj is None:
            media_obj = Media(
                tw_id = media['id_str'],
                media_url = media['media_url'],
                display_url = media['display_url']
            )
        insert(media_obj)
        tweet_obj.media.append(media_obj)
    insert(tweet_obj)

def insert(db_obj):
    global rollback_ctr
    try:
        db.session.add(db_obj)
        db.session.commit()
        rollback_ctr = 0
    except:
        sys.stderr.write('\nException rollback_ctr: ' + rollback_ctr)
        if rollback_ctr == 0:
            sys.stderr.write('\nRolling back ...')
            db.session.rollback()
            rollback_ctr += 1
        else:
            sys.stderr.write('\nResetting db.session ...')
            # reset db.session
            db.close()
            db.init_app(app)
        raise


def follow_these():
    follow = []
    streams = db.session.query(Stream).filter(Stream.active==1).all()
    if streams is None:
        return None
    for stream_obj in streams:
        for lot_obj in stream_obj.lots:
            for user_obj in lot_obj.users:
                follow.append(user_obj.tw_id)
    return follow

def catch_streams(timeout):
    while 1:
        follow = follow_these()
        if not follow:
            sys.stderr.write('No active streams, waiting '+str(timeout)+' secs.\n')
            time.sleep(timeout)
            continue
        follow_csv = ','.join(follow)
        twitter_stream = TwitterStream(auth=auth, timeout=timeout)
        last_check = int(time.time())
        sys.stderr.write('Stream catcher following: ' + repr(follow) + '\n')
        for tweet in twitter_stream.statuses.filter(follow=follow_csv, track=follow_csv):
            try:
                if tweet is None:
                    printNicely("-- None --")
                elif tweet is Timeout:
                    printNicely("-- Timeout --")
                elif tweet is HeartbeatTimeout:
                    printNicely("-- Heartbeat Timeout --")
                elif tweet is Hangup:
                    printNicely("-- Hangup --")
                elif tweet.get('text'):
                    #printNicely("-- Processing --")
                    _process_tweet(tweet)
                else:
                    sys.stderr.write('Unparsed:\n'+repr(tweet)+'\n')
                now = int(time.time())
                if now > (last_check + timeout):
                    last_check = now
                    new_follow_csv =  ','.join(follow_these())
                    if new_follow_csv != follow_csv:
                        sys.stderr.write('New follows ... restarting stream\n')
                        break
            except Exception, e:
                #sys.stderr.write(pformat(tweet)+'\n')
                sys.stderr.write(traceback.format_exc()+'\n')
                sys.stderr.write('Rolling back in main for loop ... ')
                db.session.rollback()
                #sys.stderr.write(repr(e)+'\n')

def get_lock():
    global lock_socket   # Without this our lock gets garbage collected
    lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        lock_socket.bind('\0' + os.path.basename(__file__)) # look for own proc name
        print 'Got the lock ... running.'
    except socket.error:
        print 'Lock exists, exiting.'
        sys.exit()


get_lock()
catch_streams(stream_timeout)
