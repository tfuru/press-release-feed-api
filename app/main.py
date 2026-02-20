from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
from . import models, database, services

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Press Release Feed API")

class FeedCreate(BaseModel):
    url: str

class ArticleResponse(BaseModel):
    id: int
    feed_id: int
    title: str
    link: str
    summary: Optional[str]
    published_at: datetime.datetime

    class Config:
        from_attributes = True

@app.get("/")
async def root():
    return {"message": "Press Release Feed API is running"}

@app.get("/feed", response_model=List[ArticleResponse])
async def get_feed(db: Session = Depends(database.get_db)):
    # Return latest 50 articles from all feeds, sorted by publication date descending
    articles = db.query(models.Article).order_by(
        models.Article.published_at.desc(),
        models.Article.id.desc()
    ).limit(50).all()
    return articles

@app.post("/feed")
async def create_feed(
    feed: FeedCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db)
):
    # Check if already exists
    db_feed = db.query(models.Feed).filter(models.Feed.url == feed.url).first()
    if not db_feed:
        db_feed = models.Feed(url=feed.url)
        db.add(db_feed)
        db.commit()
        db.refresh(db_feed)
        message = "Feed registered successfully"
    else:
        message = "Feed already registered"
    
    # Trigger article fetch in background
    background_tasks.add_task(services.fetch_and_store_articles, db, db_feed.id, db_feed.url)
    
    return {"feed_id": db_feed.id, "message": message, "url": db_feed.url}

@app.delete("/feed/{feed_id}")
async def delete_feed(feed_id: int, db: Session = Depends(database.get_db)):
    db_feed = db.query(models.Feed).filter(models.Feed.id == feed_id).first()
    if not db_feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    db.delete(db_feed)
    db.commit()
    return {"message": f"Feed {feed_id} deleted successfully"}
