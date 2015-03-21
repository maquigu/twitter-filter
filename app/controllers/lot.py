import simplejson as json
from flask import Blueprint, request, jsonify
import config

# Import models
from app.models import (
    Lot, 
    Tweet,
    db
)

# Define the blueprint: 'lots', set its url prefix: app.url/lots
lot_mod = Blueprint('lots', __name__, url_prefix='/lots')

@lot_mod.route('/<lot_slug>/tweets', methods=['GET'])
def get_lot_tweets(lot_slug):
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
            'user', 'lots'
        ).filter(
            Lot.slug==lot_slug
        ).paginate(page, per_page, False).items:
        tweets.append(json.loads(tweet_obj.json_str))
    return jsonify(tweets=tweets, message='success') 
