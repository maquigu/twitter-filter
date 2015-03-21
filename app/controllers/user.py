import simplejson as json
from flask import Blueprint, request, jsonify
from sqlalchemy import func
import config

# Import models
from app.models import (
    User,
    Lot, 
    Tweet,
    db
)

# Define the blueprint: 'users', set its url prefix: app.url/users
user_mod = Blueprint('users', __name__, url_prefix='/users')

@user_mod.route('/<screen_name>/tweets', methods=['GET'])
def get_user_tweets(screen_name):
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
            'user'
        ).filter(
            func.lower(User.screen_name)==func.lower(screen_name)
        ).paginate(page, per_page, False).items:
        tweets.append(json.loads(tweet_obj.json_str))
    return jsonify(tweets=tweets, message='success') 
