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
    _etag = Column(String(512))

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

class Stream(CommonColumns):
    __tablename__ = 'stream'
    name = Column(String(512))

class List(CommonColumns):
    __tablename__ = 'list'
    slug = Column(String(1024))
    name = Column(String(512))
    tw_id = Column(String(512))
    owner = relationship(Owner, uselist=False)
    
class StreamList(CommonColumns):
    __tablename__ = 'stream_list'
    stream_id = Column(Integer, ForeignKey('stream._id'), primary_key=True)
    list_id = Column(Integer, ForeignKey('list._id'), primary_key=True)

class User(CommonColumns):
    __tablename__ = 'user'
    screen_name = Column(String(512))
    tw_id = Column(String(512))
    location = Column(String(512))
    json_str = Column(Text)    

class Hashtag(CommonColumns):
    __tablename__ = 'hashtag'
    hashtag = Column(String(1024))
    timestamp = Column(DateTime)

class Mention(CommonColumns):
    __tablename__ = 'mention'
    mention = Column(String(512))
    timestamp = Column(DateTime)

class Share(CommonColumns):
    __tablename__ = 'share'
    share = Column(String(2048))
    timestamp = Column(DateTime) 

class Tweet(CommonColumns):
    __tablename__ = 'tweet'
    tweet_id = Column(String(512))
    timestamp = Column(DateTime)
    user = relationship(User)
    hashtags = relationship(Hashtag)
    mentions = relationship(Mention)
    shares = relationship(Share)
    json_str = Column(Text)

