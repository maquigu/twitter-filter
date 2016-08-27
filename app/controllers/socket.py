import simplejson as json
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
def get_stream_tweets(stream_name):
    tweets = []
    since_id = request.args.get('since_id')
    max_id = request.args.get('max_id')
    count = request.args.get('count')
    direction = request.args.get('direction')
    if direction == 'new': # Means we're going forward 
        if since_id is None:
            since_id = '0'
        for tweet_obj in Tweet.query.join(
                'user', 'lots', 'streams'
            ).filter(
                Stream.name == stream_name, Tweet.tw_id > since_id
            ).order_by(Tweet.tw_id.desc()).limit(count).all():
            tweets.append(json.loads(tweet_obj.json_str))
    elif direction == 'old' and max_id is not None: # Means we're going backwards
        for tweet_obj in Tweet.query.join(
                'user', 'lots', 'streams'
            ).filter(
                Stream.name == stream_name, Tweet.tw_id < max_id
            ).order_by(Tweet.tw_id.desc()).limit(count).all():
            tweets.append(json.loads(tweet_obj.json_str))
    return jsonify(
        tweets=tweets, max_id=max_id, since_id=since_id,
        direction=direction, message='success'
    ) 

@socket_mod.route('/all-metrics')
def get_stream_tweets_and_metrics(stream_name):
    filters = get_filters(stream_name)
    tweets, max_id, since_id = query.filter_tweets(filters, config.TWEETS_PER_PAGE)
    return jsonify(
        tweets=tweets, max_id=max_id, since_id=since_id, direction="new",
        total=stream_total(stream_name), top_users=user_metrics(filters),
        top_hashtags=hashtag_metrics(filters), top_lots=lot_metrics(filters),
        top_urls=url_metrics(filters), message='success'
    )


@socket_mod.route('/user-metrics')
def get_stream_user_metrics(stream_name):
    filters = get_filters(stream_name)
    metrics = query.user_metrics(filters)
    return jsonify(
        metrics=metrics, filters=filters, message='success'
    ) 

@socket_mod.route('/lot-metrics')
def get_stream_lot_metrics(stream_name):
    filters = get_filters(stream_name)
    metrics = query.lot_metrics(filters)
    return jsonify(
        metrics=metrics, filters=filters, message='success'
    ) 

@socket_mod.route('/hashtag-metrics')
def get_stream_hashtag_metrics(stream_name):
    filters = get_filters(stream_name)
    metrics = query.hashtag_metrics(filters)
    return jsonify(
        metrics=metrics, filters=filters, message='success'
    )

@socket_mod.route('/url-metrics')
def get_stream_url_metrics(stream_name):
    filters = get_filters(stream_name)
    metrics = query.url_metrics(filters)
    return jsonify(
        metrics=metrics, filters=filters, message='success'
    )

