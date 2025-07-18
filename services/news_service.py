"""
News service for managing news articles and background polling.

This module handles:
- In-memory news storage
- Background RSS polling
- News retrieval and filtering operations
"""

from __future__ import annotations

import asyncio
import datetime as dt
from typing import List, Optional

from core.config import settings
from models.news import FeedState, NewsItem
from services.rss_fetcher import fetch_feed


class NewsService:
    """
    Service class for managing news articles and RSS feed polling.
    
    Handles in-memory storage of news articles and provides methods
    for retrieving, filtering, and managing news data.
    """
    
    def __init__(self):
        self.news_store: List[NewsItem] = []
        self.feed_state = FeedState()
        self._polling_task: Optional[asyncio.Task] = None
    
    async def start_polling(self) -> None:
        """Start the background RSS polling task."""
        if self._polling_task is None or self._polling_task.done():
            self._polling_task = asyncio.create_task(self._rss_poller())
    
    async def stop_polling(self) -> None:
        """Stop the background RSS polling task."""
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
    
    async def _rss_poller(self) -> None:
        """Background task that polls the RSS feed every configured interval."""
        
        print(f"[{dt.datetime.now():%H:%M:%S}] Starting RSS poller for BBC Middle East...")
        
        while True:
            try:
                new_items = await fetch_feed(settings.BBC_MIDDLE_EAST_RSS, self.feed_state)
                
                # Add new items to the front of the list (most recent first)
                for item in new_items:
                    self.news_store.insert(0, item)
                    print(f"[{item.published:%Y-%m-%d %H:%M}] {item.title}")
                
                # Keep only last N articles to prevent memory issues
                if len(self.news_store) > settings.MAX_STORED_ARTICLES:
                    self.news_store = self.news_store[:settings.MAX_STORED_ARTICLES]
                    
            except Exception as e:
                print(f"[{dt.datetime.now():%H:%M:%S}] RSS poller error: {e}")
            
            # Wait for configured interval before next poll
            await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)
    
    def get_all_news(self) -> List[NewsItem]:
        """Get all stored news articles."""
        return self.news_store.copy()
    
    def get_latest_news(self, count: int = 10) -> List[NewsItem]:
        """
        Get the latest N news articles.
        
        Args:
            count: Number of articles to return (default: 10)
            
        Returns:
            List of latest NewsItem objects
        """
        return self.news_store[:min(count, len(self.news_store))]
    
    def search_news(self, keyword: str) -> List[NewsItem]:
        """
        Search news articles by keyword in title or summary.
        
        Args:
            keyword: Search term to look for
            
        Returns:
            List of matching NewsItem objects
        """
        keyword_lower = keyword.lower()
        return [
            item for item in self.news_store
            if keyword_lower in item.title.lower() or keyword_lower in item.summary.lower()
        ]
    
    def get_feed_status(self) -> dict:
        """
        Get RSS feed polling status and statistics.
        
        Returns:
            Dictionary with feed statistics and status
        """
        return {
            "feed_url": settings.BBC_MIDDLE_EAST_RSS,
            "total_articles_stored": len(self.news_store),
            "unique_articles_seen": len(self.feed_state.seen_ids),
            "last_etag": self.feed_state.etag,
            "last_modified": self.feed_state.modified,
            "latest_article": self.news_store[0].to_dict() if self.news_store else None,
            "polling_active": self._polling_task is not None and not self._polling_task.done()
        }


# Global news service instance
news_service = NewsService() 