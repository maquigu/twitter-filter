import simplejson as json
import logging as log
import sys
from flask import Blueprint, request, jsonify
import config
from sqlalchemy import func

# Import models
from app.models import (
    Stream, 
    StreamLot,
    Lot, 
    LotUser,
    Owner,
    User,
    Tweet,
    TweetHashtag,
    Hashtag,
    TweetURL,
    URL,
    TweetMention,
    Mention,
    TweetMedia,
    Media,
    db
)

# Import model queries
from app.models import query

# Define the blueprint: 'streams', set its url prefix: app.url/streams
socket_mod = Blueprint('sockets', __name__, url_prefix='/sockets')

@socket_mod.route('/tweets')
def get_stream_tweets(ws):
    while not ws.closed:
        try:
            message = json.loads(ws.receive())
            if "filters" in message:
                filters = message["filters"]
            else:
                filters = {}
            max_id = message.get("max_id", None)
            since_id = message.get("since_id", None)
            count = message.get("count", None)
            direction = message.get("direction", None)
            tweets, max_id, since_id = query.filter_tweets(filters, max_id, since_id, count, direction)
            json_out = jsonify(
                tweets=tweets, max_id=max_id, since_id=since_id,
                direction=direction, message='success'
            )
            log.info("Socket Out:", json_out)
            ws.send(json_out)
        except Exception, e:
            log.critical("WS Error in tweets: "+repr(e))
            ws.send(jsonify(message='error', details=repr(e)))

@socket_mod.route('/metrics')
def get_stream_tweets_and_metrics(ws):
    while not ws.closed:
        try:
            message = json.loads(ws.receive())
            if "filters" in message:
                filters = message["filters"]
            else:
                filters = {}
            tweets, max_id, since_id = query.filter_tweets(filters, config.TWEETS_PER_PAGE)
            ws.send(jsonify(
                total=query.stream_total(stream_name), top_users=query.user_metrics(filters),
                top_hashtags=query.hashtag_metrics(filters), top_lots=query.lot_metrics(filters),
                top_urls=query.url_metrics(filters), message='success'
            ))
        except Exception, e:
            ws.send(jsonify(message='error', details=repr(e)))


