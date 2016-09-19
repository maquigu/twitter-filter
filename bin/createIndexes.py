#!/usr/bin/env python
import sys
from sqlalchemy import Index
from sqlalchemy import create_engine
from app.models import (
    User,
    Lot,
    Stream,
    Hashtag,
    Mention,
    URL,
    Media,
    Tweet,
)
import config

engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

ix_list = [
    Index('ix_stream_name', Stream.name, unique=True),
    Index('ix_user_screen_name', User.screen_name, unique=True),
    Index('ix_lot_name', Lot.name),
    Index('ix_hashtag_text', Hashtag.text),
    Index('ix_url_expanded_url', URL.expanded_url),
    Index('ix_tweet_created_at', Tweet.created_at),
]

for ix in ix_list:
    try:
        ix.create(engine)
    except Exception, e:
        print 'Exception:', repr(e)

