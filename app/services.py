import feedparser
import httpx
from sqlalchemy.orm import Session
from . import models
import datetime
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

async def fetch_and_store_articles(db: Session, feed_id: int, url: str):
    try:
        async with httpx.AsyncClient(follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as client:
            response = await client.get(url, timeout=15.0)
            response.raise_for_status()
            
        content_type = response.headers.get("content-type", "").lower()
        
        # Check if it looks like an RSS/Atom feed
        if "xml" in content_type or "rss" in content_type or "atom" in content_type or url.endswith((".xml", ".rdf", ".rss", ".atom")):
            await parse_rss_feed(db, feed_id, response.text)
        elif "prtimes.jp" in url:
            # Custom scraping for PR TIMES
            await scrape_prtimes(db, feed_id, url, response.text)
        else:
            logger.warning(f"Unsupported content type or URL for fetching: {url} ({content_type})")

    except Exception as e:
        logger.error(f"Error fetching articles from {url}: {e}")
        db.rollback()

async def parse_rss_feed(db: Session, feed_id: int, text: str):
    feed_data = feedparser.parse(text)
    if not feed_data.entries:
        return

    for entry in feed_data.entries:
        link = entry.get("link")
        if not link:
            continue
            
        db_article = db.query(models.Article).filter(models.Article.link == link).first()
        if db_article:
            continue
        
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime.datetime(*entry.published_parsed[:6])
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            published = datetime.datetime(*entry.updated_parsed[:6])
        
        new_article = models.Article(
            feed_id=feed_id,
            title=entry.get("title", "No Title"),
            link=link,
            summary=entry.get("summary", ""),
            published_at=published or datetime.datetime.utcnow()
        )
        db.merge(new_article)
    db.commit()

async def scrape_prtimes(db: Session, feed_id: int, base_url: str, html: str):
    soup = BeautifulSoup(html, "html.parser")
    
    # PR TIMES technology specific structure
    # Based on browser observation: a.list-article__link contains the info
    articles = soup.select("a.list-article__link")
    
    for art in articles:
        link_suffix = art.get("href")
        if not link_suffix:
            continue
        link = urljoin("https://prtimes.jp", link_suffix)
        
        db_article = db.query(models.Article).filter(models.Article.link == link).first()
        if db_article:
            continue
            
        title_tag = art.select_one("h3")
        title = title_tag.get_text(strip=True) if title_tag else "No Title"
        
        # Time parsing
        time_tag = art.select_one("time")
        published_at = datetime.datetime.utcnow()
        if time_tag and time_tag.get("datetime"):
            try:
                # Example: 2024-02-20T21:00:00+09:00 -> 2024-02-20 21:00:00
                dt_str = time_tag.get("datetime")
                # Handle ISO format with timezone
                published_at = datetime.datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            except Exception:
                pass
        
        new_article = models.Article(
            feed_id=feed_id,
            title=title,
            link=link,
            summary="", # Summary is usually not in the list view
            published_at=published_at
        )
        db.merge(new_article)
    db.commit()
