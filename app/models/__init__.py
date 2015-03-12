from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base
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
    UniqueConstraint)

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

class Owner(CommonColumns):
    __tablename__ = 'owner'
    screen_name = Column(String(512))

class User(CommonColumns):
    __tablename__ = 'user'
    screen_name = Column(String(512))
    tw_id = Column(String(512))
    location = Column(String(512))
    json_str = Column(Text)    

class LotUser(CommonColumns):
    __tablename__ = 'lot_user'
    lot_id = Column(Integer, ForeignKey('lot._id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('user._id'), primary_key=True)
    #user = relationship(User)

class Lot(CommonColumns):
    __tablename__ = 'lot'
    slug = Column(String(1024))
    name = Column(String(512))
    tw_id = Column(String(512))
    owner_id = Column(Integer, ForeignKey('owner._id'))
    owner = relationship(Owner, uselist=False)
    users = relationship(User, secondary='lot_user')

class StreamLot(CommonColumns):
    __tablename__ = 'stream_lot'
    stream_id = Column(Integer, ForeignKey('stream._id'), primary_key=True)
    lot_id = Column(Integer, ForeignKey('lot._id'), primary_key=True)
    #lot = relationship(Lot)

class Stream(CommonColumns):
    __tablename__ = 'stream'
    name = Column(String(512))
    lots = relationship(Lot, secondary='stream_lot')

class Hashtag(CommonColumns):
    __tablename__ = 'hashtag'
    hashtag = Column(String(1024))
    timestamp = Column(DateTime)

class TweetHashtag(CommonColumns):
    __tablename__ = 'tweet_hashtag'
    tweet_id = Column(Integer, ForeignKey('tweet._id'), primary_key=True)
    hashtag_id = Column(Integer, ForeignKey('hashtag._id'), primary_key=True)
    #hashtag = relationship(Hashtag)

class Mention(CommonColumns):
    __tablename__ = 'mention'
    mention = Column(String(512))
    timestamp = Column(DateTime)

class TweetMention(CommonColumns):
    __tablename__ = 'tweet_mention'
    tweet_id = Column(Integer, ForeignKey('tweet._id'), primary_key=True)
    mention_id = Column(Integer, ForeignKey('mention._id'), primary_key=True)
    #mention = relationship(Mention)
    
class Share(CommonColumns):
    __tablename__ = 'share'
    share = Column(String(2048))
    timestamp = Column(DateTime) 

class TweetShare(CommonColumns):
    __tablename__ = 'tweet_share'
    tweet_id = Column(Integer, ForeignKey('tweet._id'), primary_key=True)
    share_id = Column(Integer, ForeignKey('share._id'), primary_key=True)
    #share = relationship(Share)

class Tweet(CommonColumns):
    __tablename__ = 'tweet'
    tweet_id = Column(String(512))
    timestamp = Column(DateTime)
    json_str = Column(Text)
    user_id = Column(Integer, ForeignKey('user._id'))
    user = relationship(User)
    hashtags = relationship(Hashtag, secondary='tweet_hashtag')
    mentions = relationship(Mention, secondary='tweet_mention')
    shares = relationship(Share, secondary='tweet_share')

