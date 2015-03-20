#!/usr/bin/env python
import sys
from app.models import (
    CommonColumns,
    Owner,
    User,
    LotUser,
    Lot,
    StreamLot,
    Stream,
    Hashtag,
    TweetHashtag,
    Mention,
    TweetMention,
    URL,
    TweetURL,
    Media,
    TweetMedia,
    Tweet,
    app,
    db
)
db.drop_all(app=app)
db.create_all(app=app)
