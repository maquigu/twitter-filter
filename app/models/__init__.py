from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.ext import hybrid
from sqlalchemy.orm import column_property, relationship, backref
from sqlalchemy import func
from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    Text,
    DateTime,
    UniqueConstraint,
    Index
)

Base = declarative_base()

class CommonColumns(Base):
    __abstract__ = True
    _id = Column(Integer, primary_key=True, autoincrement=True)
    _created = Column(DateTime, default=func.now())
    _updated = Column(DateTime, default=func.now(), onupdate=func.now())

    def dictify(self):
        """
        Used to dump related objects to dict
        """
        relationships = inspect(self.__class__).relationships.keys()
        mapper = inspect(self)
        attrs = [a.key for a in mapper.attrs if \
                a.key not in relationships \
                and not a.key in mapper.expired_attributes]
        attrs += [a.__name__ for a in inspect(self.__class__).all_orm_descriptors if a.extension_type is hybrid.HYBRID_PROPERTY]
        return dict([(c, getattr(self, c, None)) for c in attrs])

class TwId(object):
    tw_id = Column(String(512))
    @declared_attr
    def __table_args__(cls):
        return (Index('ix_%s_tw_id' % cls.__tablename__, 'tw_id', unique=True),)

class Owner(CommonColumns, TwId):
    __tablename__ = 'owner'
    screen_name = Column(String(512))

class User(CommonColumns, TwId):
    __tablename__ = 'user'
    screen_name = Column(String(512), index=True)
    location = Column(String(512))
    json_str = Column(Text)    

class LotUser(CommonColumns):
    __tablename__ = 'lot_user'
    lot_id = Column(Integer, ForeignKey('lot._id'))
    user_id = Column(Integer, ForeignKey('user._id'))

class Lot(CommonColumns, TwId):
    __tablename__ = 'lot'
    slug = Column(String(512), index=True)
    name = Column(String(512))
    owner_id = Column(Integer, ForeignKey('owner._id'))
    owner = relationship(Owner, uselist=False)
    users = relationship(User, secondary='lot_user', backref='lots')

class StreamLot(CommonColumns):
    __tablename__ = 'stream_lot'
    stream_id = Column(Integer, ForeignKey('stream._id'))
    lot_id = Column(Integer, ForeignKey('lot._id'))

class Stream(CommonColumns):
    __tablename__ = 'stream'
    name = Column(String(512))
    lots = relationship(Lot, secondary='stream_lot', backref='streams')

class Hashtag(CommonColumns):
    __tablename__ = 'hashtag'
    text = Column(String(512), index=True)

class TweetHashtag(CommonColumns):
    __tablename__ = 'tweet_hashtag'
    tweet_id = Column(Integer, ForeignKey('tweet._id'))
    hashtag_id = Column(Integer, ForeignKey('hashtag._id'))

class Media(CommonColumns, TwId):
    __tablename__ = 'media'
    media_url = Column(String(512), index=True)
    display_url = Column(String(2048))
    type = Column(String(512))

class TweetMedia(CommonColumns):
    __tablename__ = 'tweet_media'
    tweet_id = Column(Integer, ForeignKey('tweet._id'))
    media_id = Column(Integer, ForeignKey('media._id'))

class Mention(CommonColumns, TwId):
    __tablename__ = 'mention'
    screen_name = Column(String(512), index=True)
    name = Column(String(1024))

class TweetMention(CommonColumns):
    __tablename__ = 'tweet_mention'
    tweet_id = Column(Integer, ForeignKey('tweet._id'))
    mention_id = Column(Integer, ForeignKey('mention._id'))
    
class URL(CommonColumns):
    __tablename__ = 'url'
    url = Column(String(512), index=True)
    display_url = Column(String(2048))
    expanded_url = Column(String(2048))

class TweetURL(CommonColumns):
    __tablename__ = 'tweet_url'
    tweet_id = Column(Integer, ForeignKey('tweet._id'))
    url_id = Column(Integer, ForeignKey('url._id'))

class Tweet(CommonColumns, TwId):
    __tablename__ = 'tweet'
    created_at = Column(DateTime)
    json_str = Column(Text)
    user_id = Column(Integer, ForeignKey('user._id'))
    user = relationship(User)
    hashtags = relationship(Hashtag, secondary='tweet_hashtag', backref='tweets')
    mentions = relationship(Mention, secondary='tweet_mention', backref='tweets')
    urls = relationship(URL, secondary='tweet_url', backref='tweets')
    media = relationship(Media, secondary='tweet_media', backref='tweets')
