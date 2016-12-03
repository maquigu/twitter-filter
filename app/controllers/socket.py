import simplejson as json
import sys
from flask import Blueprint, request, jsonify
import config
from sqlalchemy import func
import gevent

from app import log

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

# Define the blueprint: "streams", set its url prefix: app.url/streams
socket_mod = Blueprint("sockets", __name__, url_prefix="/sockets")

def tweet_fetcher(ws, filters, max_id, since_id, count, direction, poll_new):
    while not ws.closed:
        log.debug( 'Fetching tweets ...')
        tweets, new_max_id, new_since_id = query.filter_tweets(filters, max_id, since_id, count, direction)
        if new_since_id != 0 and new_max_id != 0:
            log.debug( 'Pushing '+str(len(tweets))+' new tweets')
            json_out = json.dumps({
                "filters": filters,
                "tweets":tweets, 
                "max_id":new_max_id, 
                "since_id":new_since_id,
                "direction":direction,
                "status":"success"
            })
            ws.send(json_out)
            if direction == "new":
                since_id = new_max_id
        if direction == "new" and poll_new:  
            gevent.sleep(30)
        else:
            return


@socket_mod.route("/tweets")
def get_stream_tweets(ws):
    poll_new = False
    filters = {}
    new_fetcher_running = False
    while not ws.closed:
        try:
            payload = ws.receive()
            if payload is None:
                return
            message = json.loads(payload)
            log.debug("Tweets Message: "+repr(message))
            if "filters" in message:
                filters = message["filters"]
            max_id = message.get("max_id", None)
            since_id = message.get("since_id", None)
            count = message.get("count", config.TWEETS_PER_PAGE)
            direction = message.get("direction", None)
            if new_fetcher_running or direction != "new":
                poll_new = False
                tweet_fetcher(ws, filters, max_id, since_id, count, direction, poll_new)
            else:
                log.debug("Polling for new tweets ...")
                poll_new = True
                threads = [gevent.spawn(tweet_fetcher, ws, filters, max_id, since_id, count, direction, poll_new)]
                gevent.joinall(threads)
            if poll_new:
                new_fetcher_running = True
        except Exception, e:
            log.exception("WS Error in tweets: "+repr(e))
            json_out = json.dumps({
                "status": "error",
                "message": repr(e)
            })
            ws.send(json_out)

@socket_mod.route("/metrics")
def get_stream_metrics(ws):
    while not ws.closed:
        try:
            payload = ws.receive()
            if payload is None:
                return
            message = json.loads(payload)
            filters = message.get("filters", {})
            stream_name = filters.get("stream_name", None)
            if stream_name is None:
                return
            start_date, end_date, total = query.stream_total(stream_name)
            json_out = json.dumps({
                "metrics": {
                    "filters": filters,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_tweets": total, 
                    "top_users": query.user_metrics(filters),
                    "top_hashtags": query.hashtag_metrics(filters),
                    "top_lots": query.lot_metrics(filters),
                    "top_urls": query.url_metrics(filters)
                },
                "status":"success"
            })
            ws.send(json_out)
        except Exception, e:
            log.exception("WS Error in Metrics: "+repr(e))
            json_out = json.dumps({
                "status": "error",
                "message": repr(e)
            })
            ws.send(json_out)


