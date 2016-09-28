import config
from sqlalchemy import func
from sqlalchemy import distinct
import simplejson as json

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

from app import log

# set_query_filters sets the query filters based on above 
def set_query_filters(q, stream_name=None, users=[], lots=[], hashtags=[], urls=[], start=[], end=[]):
    if stream_name:
        q = q.filter(Stream.name == stream_name)
    if users:
        q = q.filter(User._id.in_(users))
    if lots:
        q = q.filter(Lot._id.in_(lots))
    if hashtags:
        q = q.filter(Hashtag._id.in_(hashtags))
    if urls:
        q = q.filter(URL._id.in_(urls))
    if start:
        q = q.filter(Tweet.created_at >= start_timestamp)
    if end and end is not "now":
        q = q.filter(Tweet.created_at <= end_timestamp)
    return q

def user_metrics(filters):
    metrics = []
    q = db.session.query(User._id, User.screen_name, func.count(Tweet.tw_id).label('tweet_count')). \
        join(Tweet). \
        join(LotUser). \
        join(Lot). \
        join(StreamLot). \
        join(Stream)
    q = set_query_filters(q, **filters)
    q = q.group_by(User.screen_name).order_by('tweet_count DESC').limit(config.TOP_N)
    #log.debug("QUERY: %s\n" % str(q))
    for r in q.all():
        #sys.stderr.write("ROW: %s\n" % repr(r))
        um = {
            "id": r[0],
            "name": r[1],
            "tweets": r[2]
        }
        metrics.append(um)
    return metrics

def lot_metrics(filters):
    metrics = []
    q = db.session.query(Lot._id, Lot.name, func.count(distinct(User._id)), func.count(Tweet.tw_id).label('tweet_count')). \
        join(LotUser). \
        join(User). \
        join(Tweet). \
        join(StreamLot). \
        join(Stream)
    q = set_query_filters(q, **filters)
    q = q.group_by(Lot.name).order_by('tweet_count DESC').limit(config.TOP_N)
    for r in q.all():
        um = {
            "id": r[0],
            "name": r[1],
            "members": r[2],
            "tweets": r[3]
        }
        metrics.append(um)
    return metrics

def hashtag_metrics(filters):
    metrics = []
    q = db.session.query(Hashtag._id, Hashtag.text, func.count(Tweet.tw_id).label('tweet_count')). \
        join(TweetHashtag). \
        join(Tweet). \
        join(User). \
        join(LotUser). \
        join(Lot). \
        join(StreamLot). \
        join(Stream)
    q = set_query_filters(q, **filters)
    q = q.group_by(Hashtag.text).order_by('tweet_count DESC').limit(config.TOP_N)
    #sys.stderr.write("QUERY: %s\n" % str(q))
    for r in q.all():
        #sys.stderr.write("ROW: %s\n" % repr(r))
        hm = {
            "id": r[0],
            "name": r[1],
            "tweets": r[2]
        }
        metrics.append(hm)
    return metrics

def url_metrics(filters):
    metrics = []
    q = db.session.query(URL._id, URL.expanded_url, func.count(Tweet.tw_id).label('tweet_count')). \
        join(TweetURL). \
        join(Tweet). \
        join(User). \
        join(LotUser). \
        join(Lot). \
        join(StreamLot). \
        join(Stream)
    q = set_query_filters(q, **filters)
    q = q.group_by(URL.expanded_url).order_by('tweet_count DESC').limit(config.TOP_N)
    for r in q.all():
        m = {
            "id": r[0],
            "name": r[1],
            "tweets": r[2]
        }
        metrics.append(m)
    return metrics


def stream_total(stream_name):
    q = db.session.query(func.min(Tweet.created_at), func.max(Tweet.created_at), func.count(Tweet.tw_id).label('tweet_count')).\
        join(User). \
        join(LotUser). \
        join(Lot). \
        join(StreamLot). \
        join(Stream)
    q = set_query_filters(q, stream_name=stream_name)
    return q.one()

def filter_tweets(filters, max_id, since_id, count, direction):
    tweets = []
    tw_id_max = 0
    tw_id_min = 0
    q = db.session.query(Tweet.tw_id, Tweet.json_str).\
        join(User). \
        join(LotUser). \
        join(Lot). \
        join(StreamLot). \
        join(Stream)
    q = set_query_filters(q, **filters)
    if direction == 'new' and since_id is not None: # Going forward in time
        q = q.filter(Tweet.tw_id > since_id)
    elif direction == 'old' and max_id is not None: # Means we're going backwards
        q = q.filter(Tweet.tw_id < max_id)
    for r in q.order_by(Tweet.tw_id.desc()).limit(count).all():
        tweets.append(json.loads(r[1]))
        if tw_id_max == 0 or r[0] > tw_id_max:
            tw_id_max = r[0]
        elif tw_id_min == 0 or r[0] < tw_id_min:
            tw_id_min = r[0]
    return tweets, tw_id_max, tw_id_min

