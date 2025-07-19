import asyncio
from typing import List, Optional
from collections import deque
import logging

from core.config import settings
from models.news import FeedState, NewsItem
from models.semantic_search import SemanticSearchResult
from services.rss_fetcher import fetch_feed
from services.semantic_search import semantic_search_service
from services.telegram_service import telegram_bot

logging.basicConfig(
    format=settings.LOG_FORMAT,
    datefmt=settings.LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class NewsService:
    """
    Service class for managing news articles and RSS feed polling.
    
    Handles in-memory storage of news articles and provides methods
    for retrieving, filtering, and managing news data.
    """
    
    def __init__(self):
        self.news_store: deque[NewsItem] = deque(maxlen=settings.MAX_STORED_ARTICLES)
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
        logger.info("Starting RSS poller for BBC Middle East...")
        
        while True:
            try:
                new_items = await fetch_feed(settings.BBC_MIDDLE_EAST_RSS, self.feed_state)
                
                if new_items:
                    logger.info(f"=== Processing {len(new_items)} new articles ===")
                    
                    for item in new_items:
                        self.news_store.appendleft(item)
                        logger.info(f"[{item.published:%Y-%m-%d %H:%M}] {item.title}")
                        
                        # try:
                        #     await telegram_bot.send_news(item)
                        # except Exception as e:
                        #     logger.error(f"Failed to send article to Telegram: {e}")
                                        
                    if len(self.news_store) > settings.MAX_STORED_ARTICLES:
                        logger.info(f"Trimming to {settings.MAX_STORED_ARTICLES} articles")
                        self.news_store = deque(
                            list(self.news_store)[:settings.MAX_STORED_ARTICLES], 
                            maxlen=settings.MAX_STORED_ARTICLES
                        )
                
            except Exception as e:
                logger.error(f"RSS poller error: {e}")
            
            await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)
    
    def get_all_news(self) -> List[NewsItem]:
        """Get all stored news articles sorted by published date (newest first)."""
        return sorted(self.news_store, key=lambda x: x.published, reverse=True)
    
    def get_latest_news(self, count: int = 10) -> List[NewsItem]:
        """
        Get the latest N news articles.
        
        Args:
            count: Number of articles to return (default: 10)
            
        Returns:
            List of latest NewsItem objects sorted by published date (newest first)
        """
        sorted_news = sorted(self.news_store, key=lambda x: x.published, reverse=True)
        return sorted_news[:min(count, len(sorted_news))]
    
    def search_news(self, keyword: str) -> List[NewsItem]:
        """
        Search news articles by keyword in title or summary.
        Results are sorted by published date (newest first).
        """
        keyword_lower = keyword.lower()
        matching_items = [
            item for item in self.news_store
            if (item.title and keyword_lower in item.title.lower()) or 
               (item.summary and keyword_lower in item.summary.lower())
        ]
        return sorted(matching_items, key=lambda x: x.published, reverse=True)

    def semantic_search(
        self, 
        query: str,
        min_threshold: float = 0.5,
        title_weight: Optional[float] = None,
        summary_weight: Optional[float] = None,
        max_results: int = 10
    ) -> List[SemanticSearchResult]:
        """
        Search news articles using semantic similarity with fine-tuned weights and thresholds.
        """
        return semantic_search_service.search(
            query=query,
            articles=list(self.news_store),
            min_threshold=min_threshold,
            title_weight=title_weight,
            summary_weight=summary_weight,
            max_results=max_results
        )
    
    def get_feed_status(self) -> dict:
        """
        Get RSS feed polling status and statistics.
        
        Returns:
            Dictionary with feed statistics and status
        """
        sorted_news = sorted(self.news_store, key=lambda x: x.published, reverse=True) if self.news_store else []
        
        return {
            "feed_url": settings.BBC_MIDDLE_EAST_RSS,
            "total_articles_stored": len(self.news_store),
            "unique_articles_seen": len(self.feed_state.seen_ids),
            "latest_content_hash": self.feed_state.latest_hash,
            "last_fetch_time": self.feed_state.last_fetch_time.isoformat() if self.feed_state.last_fetch_time else None,
            "latest_article": sorted_news[0].to_dict() if sorted_news else None,
            "polling_active": self._polling_task is not None and not self._polling_task.done(),
        }


news_service = NewsService() 
