"""
RSS feed fetching service.

This module handles the core RSS feed fetching logic including:
- HTTP requests with conditional GET headers
- RSS/Atom feed parsing
- New item detection and deduplication
"""

from __future__ import annotations

import datetime as dt
import hashlib
from typing import List

import feedparser
import httpx

from core.config import settings
from models.news import FeedState, NewsItem


async def fetch_feed(url: str, state: FeedState) -> List[NewsItem]:
    """
    Fetch RSS feed and return only new items since last call.
    
    Uses conditional GET headers (ETag/Last-Modified) to minimize bandwidth
    and server load when the feed hasn't changed.
    
    Args:
        url: RSS feed URL to fetch
        state: FeedState object to track changes and seen items
        
    Returns:
        List of new NewsItem objects since last fetch
    """
    
    headers: dict[str, str] = {}
    if state.etag:
        headers["If-None-Match"] = state.etag
    if state.modified:
        headers["If-Modified-Since"] = state.modified

    try:
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, headers=headers)

        # 304 = Not Modified - feed hasn't changed since last poll
        if resp.status_code == 304:
            print(f"[{dt.datetime.now():%H:%M:%S}] Feed unchanged (304)")
            return []

        if resp.status_code != 200:
            print(f"[{dt.datetime.now():%H:%M:%S}] HTTP {resp.status_code} error fetching feed")
            return []

        # Parse the RSS feed
        feed = feedparser.parse(resp.text)
        
        # Update cache headers for next request
        state.etag = feed.get("etag")
        state.modified = feed.get("modified")

        fresh_items: List[NewsItem] = []
        
        for entry in feed.entries:
            # Generate unique ID for each article
            guid = entry.get("id") or hashlib.sha1(entry.link.encode()).hexdigest()
            
            # Skip if we've already seen this article
            if guid in state.seen_ids:
                continue

            state.seen_ids.add(guid)
            
            # Parse published date
            try:
                published = dt.datetime(*entry.published_parsed[:6])
            except (AttributeError, TypeError, ValueError):
                published = dt.datetime.utcnow()

            # Create NewsItem object
            fresh_items.append(
                NewsItem(
                    id=guid,
                    title=entry.title,
                    url=entry.link,
                    published=published,
                    summary=entry.get("summary", ""),
                    source=feed.feed.get("title", url),
                )
            )

        print(f"[{dt.datetime.now():%H:%M:%S}] Found {len(fresh_items)} new articles")
        return fresh_items

    except httpx.TimeoutException:
        print(f"[{dt.datetime.now():%H:%M:%S}] Timeout fetching feed")
        return []
    except Exception as e:
        print(f"[{dt.datetime.now():%H:%M:%S}] Error fetching feed: {e}")
        return [] 