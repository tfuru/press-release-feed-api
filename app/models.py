from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class Feed(Base):
    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    
    articles = relationship("Article", back_populates="feed", cascade="all, delete-orphan")

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, ForeignKey("feeds.id"))
    title = Column(String)
    link = Column(String, unique=True)
    summary = Column(Text)
    published_at = Column(DateTime, default=datetime.datetime.utcnow)

    feed = relationship("Feed", back_populates="articles")
