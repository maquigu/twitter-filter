import simplejson as json
import logging as log
import sys
from flask import Blueprint, request, jsonify
import config
from sqlalchemy import func
import gevent

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

def query_for_new_tweets(ws, filters, max_id, since_id, count, direction):
    #while not ws.closed:
        tweets, new_max_id, new_since_id = query.filter_tweets(filters, max_id, since_id, count, direction)
        if new_since_id is not None and new_max_id is not None:
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
        if direction == "new":  
            gevent.sleep(30)
        else:
            return


@socket_mod.route("/tweets")
def get_stream_tweets(ws):
    while not ws.closed:
        try:
            payload = ws.receive()
            if payload is None:
                return
            message = json.loads(payload)
            log.info("Tweets Message: "+repr(message))
            if "filters" in message:
                filters = message["filters"]
            else:
                filters = {}
            max_id = message.get("max_id", None)
            since_id = message.get("since_id", None)
            count = message.get("count", config.TWEETS_PER_PAGE)
            direction = message.get("direction", None)
            query_for_new_tweets(ws, filters, max_id, since_id, count, direction)
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
            json_out = json.dumps({
                "metrics": {
                    "filters": filters,
                    "total_tweets": query.stream_total(stream_name), 
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


