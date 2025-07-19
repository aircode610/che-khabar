import datetime as dt
import hashlib
from typing import List

import feedparser
import httpx
import numpy as np
from sentence_transformers import SentenceTransformer

from core.config import settings
from models.news import FeedState, NewsItem

import logging

logger = logging.getLogger(__name__)

async def fetch_feed(url: str, state: FeedState) -> List[NewsItem]:
    """
    Fetch RSS feed and return only new items since last call.
    """
    logger.info("\n=== Starting fetch cycle ===")
    logger.info(f"Previous fetch: {state.last_fetch_time or 'Never'}")

    try:
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
            logger.info(f"Fetching from: {url}")
            resp = await client.get(url)
            
            if resp.status_code != 200:
                logger.error(f"Error status {resp.status_code}")
                return []

            feed = feedparser.parse(resp.text)
            
            latest_hash = generate_latest_hash(feed)
            
            if state.latest_hash:
                if latest_hash == state.latest_hash:
                    logger.info(f"Content unchanged (hash: {latest_hash[:8]}...)")
                    return []
                logger.info(f"Content changed (hash: {state.latest_hash[:8]}... -> {latest_hash[:8]}...)")
            else:
                logger.info(f"Initial fetch (hash: {latest_hash[:8]}...)")

            state.latest_hash = latest_hash
            state.last_fetch_time = dt.datetime.now(dt.timezone.utc)
            
            fresh_items: List[NewsItem] = []
            
            logger.info(f"Found {len(feed.entries)} entries to process")
            
            for entry in feed.entries:
                guid = str(entry.get("id") or hashlib.sha1(str(entry.link).encode()).hexdigest())
                
                if guid in state.seen_ids:
                    continue

                state.seen_ids.add(guid)
                
                try:
                    if not entry.published_parsed or not isinstance(entry.published_parsed, tuple):
                        raise ValueError("Invalid published_parsed format")
                        
                    year, month, day, hour, minute, second = entry.published_parsed[:6]
                    published = dt.datetime(year, month, day, hour, minute, second)
                except (AttributeError, TypeError, ValueError):
                    published = dt.datetime.now(dt.timezone.utc)
                    logger.warning(f"Failed to parse date for article {guid[:8]}...")

                title = str(entry.get("title")) if entry.get("title") else None
                summary = str(entry.get("summary")) if entry.get("summary") else None
                
                text_to_embed = " ".join(filter(None, [title, summary]))
                if text_to_embed:
                    tensor = settings.model.encode(text_to_embed)
                    embedding = np.array(tensor, dtype=np.float32)
                else:
                    embedding = None

                fresh_items.append(
                    NewsItem(
                        id=guid,
                        published=published,
                        title=title,
                        url=str(entry.get("link")) if entry.get("link") else None,
                        summary=summary,
                        source=str(getattr(feed.feed, 'title', None)) if getattr(feed.feed, 'title', None) else None,
                        embedding=embedding
                    )
                )

            logger.info(f"=== Fetch complete: {len(fresh_items)} articles ===\n")
            return fresh_items

    except httpx.TimeoutException:
        logger.error("Timeout fetching feed")
        return []
    except Exception as e:
        logger.error(f"Error fetching feed: {e}")
        return []

def generate_latest_hash(feed: feedparser.FeedParserDict) -> str:
    """Generate a hash based only on the latest article's data."""
    if not feed.entries:
        return ""
    
    latest = feed.entries[0]
    latest_data = (
        latest.get("id", ""),
        latest.get("title", ""),
        latest.get("link", ""),
        latest.get("published", ""),
    )
    
    return hashlib.sha1(str(latest_data).encode()).hexdigest() 
    