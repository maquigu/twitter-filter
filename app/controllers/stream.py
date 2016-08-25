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

# Import celery tasks
from app.celery import buffer_tasks, catcher_tasks

# Define the blueprint: 'streams', set its url prefix: app.url/streams
stream_mod = Blueprint('streams', __name__, url_prefix='/streams')

@stream_mod.route('/', methods=['POST'])
def create():
    req = json.loads(request.data) 
    if isinstance(req, dict) and 'stream_name' in req:
        stream_name = req['stream_name']
        resp = {
            'lots': [],
            'stream_name': stream_name
        }
        stream_obj = db.session.query(Stream).filter(Stream.name==stream_name).first()
        if stream_obj is None:
            stream_obj = Stream(name=stream_name)
        stream_lists = req.get('lists', [])
        for lot_dict in stream_lists:
            if not isinstance(lot_dict, dict):
                continue
            lot_obj = db.session.query(Lot).filter(Lot.slug==lot_dict.get('slug')).first()
            if lot_obj is None:
                lot_obj = Lot(
                    slug=lot_dict.get('slug'),
                    name=lot_dict.get('name'),
                    tw_id=lot_dict.get('twitter_id'),
                    owner=Owner(screen_name=lot_dict.get('owner'))
                )
            resp['lots'].append(lot_obj.dictify())
            stream_obj.lots.append(lot_obj)
        db.session.add(stream_obj)
        db.session.commit()
        resp['created'] = True
        buffer_tasks.on_create_stream.apply_async(
            args=[req],
            queue=config.CELERY_BUFFER_QUEUE
        )
        return  jsonify(response=resp, message='success')
    else:
        return jsonify(stream_name=None, message='stream_name required.')

@stream_mod.route('/<stream_name>/tweets', methods=['GET'])
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

@stream_mod.route('/<stream_name>/tweets+metrics', methods=['GET'])
def get_stream_tweets_and_metrics(stream_name):
    filters = get_filters(stream_name)
    tweets, max_id, since_id = filter_tweets(filters, count)
    return jsonify(
        tweets=tweets, max_id=max_id, since_id=since_id, direction="new",
        total=stream_total(), user_metrics=user_metrics(filters),
        hashtag_metrics=hashtag_metrics(filters), lot_metrics=lot_metrics(filters),
        url_metrics=url_metrics(filters), message='success'
    )


@stream_mod.route('/<stream_name>/user-metrics', methods=['GET'])
def get_stream_user_metrics(stream_name):
    filters = get_filters(stream_name)
    metrics = user_metrics(filters)
    return jsonify(
        metrics=metrics, filters=filters, message='success'
    ) 

@stream_mod.route('/<stream_name>/lot-metrics', methods=['GET'])
def get_stream_lot_metrics(stream_name):
    filters = get_filters(stream_name)
    metrics = lot_metrics(filters)
    return jsonify(
        metrics=metrics, filters=filters, message='success'
    ) 

@stream_mod.route('/<stream_name>/hashtag-metrics', methods=['GET'])
def get_stream_hashtag_metrics(stream_name):
    filters = get_filters(stream_name)
    metrics = hashtag_metrics(filters)
    return jsonify(
        metrics=metrics, filters=filters, message='success'
    )

@stream_mod.route('/<stream_name>/url-metrics', methods=['GET'])
def get_stream_url_metrics(stream_name):
    filters = get_filters(stream_name)
    metrics = url_metrics(filters)
    return jsonify(
        metrics=metrics, filters=filters, message='success'
    )


@stream_mod.route('/<stream_name>/tweets-page', methods=['GET'])
def get_stream_tweets_page(stream_name):
    tweets = []
    page = request.args.get('page')
    if page is None:
        page = 1
    else:
        page = int(page)
    per_page = request.args.get('per_page')
    if per_page is None:
        per_page = config.TWEETS_PER_PAGE 
    else:
        per_page = int(per_page)
    for tweet_obj in Tweet.query.join(
            'user', 'lots', 'streams'
        ).filter(
            Stream.name==stream_name
        ).paginate(page, per_page, False).items:
        tweets.append(json.loads(tweet_obj.json_str))
    return jsonify(tweets=tweets, message='success') 

# get_filters grabs the filters from request.args
def get_filters(stream_name):
    filters = {
        "stream_name": stream_name,
    }
    start_timestamp = request.args.get('start')
    end_timestamp = request.args.get('end')
    # These are lists, specified via multiple html params of the same name
    users = request.args.getlist('user_id')
    lots = request.args.getlist('lot_id')
    hashtags = request.args.getlist('hashtag_id')
    shares = request.args.getlist('share_id')
    if users:
        filters["users"] = users
    if lots:
        filters["lots"] = lots
    if hashtags:
        filters["hashtags"] = hashtags
    if shares:
        filters["shares"] = shares
    if start_timestamp is not None:
        filters["start"] = start_timestamp
    if end_timestamp is not None and not "now":
        filters["end"] = end_timestamp
    return filters
    
# set_query_filters sets the query filters based on above 
def set_query_filters(q, stream_name=None, users=[], lots=[], hashtags=[], shares=[], start=[], end=[]):
    if stream_name:
        q = q.filter(Stream.name == stream_name)
    if users:
        q = q.filter(User._id.in_(users))
    if lots:
        q = q.filter(Lot._id.in_(lots))
    if hashtags:
        q = q.filter(Hashtag._id.in_(hashtags))
    if shares:
        q = q.join(TweetMedia).join(Media)
        q = q.filter(Media._id.in_(shares))
    if start:
        q = q.filter(Tweet.created_at >= start_timestamp)
    if end and end is not "now":
        q = q.filter(Tweet.created_at <= end_timestamp)
    return q

def user_metrics(filters):
    metrics = []
    q = db.session.query(User._id, User.screen_name, func.count(Tweet.tw_id)). \
        join(Tweet). \
        join(LotUser). \
        join(Lot). \
        join(StreamLot). \
        join(Stream)
    q = set_query_filters(q, **filters)
    q = q.group_by(User.screen_name).limit(config.TOP_N)
    #sys.stderr.write("QUERY: %s\n" % str(q))
    for r in q.all():
        #sys.stderr.write("ROW: %s\n" % repr(r))
        um = {
            "user_id": r[0],
            "screen_name": r[1],
            "tweets": r[2]
        }
        metrics.append(um)
    return metrics

def lot_metrics(filters):
    metrics = []
    q = db.session.query(Lot._id, Lot.name, func.count(Tweet.tw_id)). \
        join(LotUser). \
        join(User). \
        join(Tweet). \
        join(StreamLot). \
        join(Stream)
    q = set_query_filters(q, **filters)
    q = q.group_by(User.screen_name).limit(config.TOP_N)
    for r in q.all():
        um = {
            "lot_id": r[0],
            "lot_name": r[1],
            "tweets": r[2]
        }
        metrics.append(um)
    return metrics

def hashtag_metrics(filters):
    metrics = []
    q = db.session.query(Hashtag._id, Hashtag.text, func.count(Tweet.tw_id)). \
        join(TweetHashtag). \
        join(Tweet). \
        join(User). \
        join(LotUser). \
        join(Lot). \
        join(StreamLot). \
        join(Stream)
    q = set_query_filters(q, **filters)
    q = q.group_by(Hashtag.text).limit(config.TOP_N)
    #sys.stderr.write("QUERY: %s\n" % str(q))
    for r in q.all():
        #sys.stderr.write("ROW: %s\n" % repr(r))
        hm = {
            "hashtag_id": r[0],
            "hashtag": r[1],
            "tweets": r[2]
        }
        metrics.append(hm)
    return metrics

def url_metrics(filters):
    metrics = []
    start_timestamp = request.args.get('start')
    end_timestamp = request.args.get('end')
    q = db.session.query(URL._id, URL.expanded_url, func.count(Tweet.tw_id)). \
        join(TweetURL). \
        join(Tweet). \
        join(User). \
        join(LotUser). \
        join(Lot). \
        join(StreamLot). \
        join(Stream)
    q = set_query_filters(q, **filters)
    q = q.group_by(URL.expanded_url).limit(config.TOP_N)
    for r in q.all():
        m = {
            "url_id": r[0],
            "url": r[1],
            "tweets": r[2]
        }
        metrics.append(m)
    return metrics


def stream_total(stream_name):
    q = db.session.query(Tweet).\
        join(User). \
        join(LotUser). \
        join(Lot). \
        join(StreamLot). \
        join(Stream)
    q = set_query_filters(q, stream_name=stream_name)
    return q.count()

def filter_tweets(filters, limit):
    tweets = []
    tw_id_max = 0
    tw_id_min = 0
    q = db.session.query(Tweet.tw_id, Tweet.json_str).\
        join(User). \
        join(LotUser). \
        join(Lot). \
        join(StreamLot). \
        join(Stream).\
        limit(limit)
    q = set_query_filters(q, **filters)
    for r in q.all():
        tweets.append(json.loads(r[1]))
        if tw_id_max == 0 or r[0] > tw_id_max:
            tw_id_max = r[0]
        elif tw_id_min == 0 or r[0] < tw_id_min:
            tw_id_min = r[0]
    return tweets, tw_id_max, tw_id_min

