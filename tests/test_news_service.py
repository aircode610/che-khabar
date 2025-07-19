import asyncio
import datetime as dt
import pytest
from unittest.mock import AsyncMock, patch

from core.config import settings
from models.news import NewsItem
from services.news_service import NewsService

@pytest.fixture
def news_service():
    """Create a fresh NewsService instance for each test."""
    return NewsService()

@pytest.fixture
def sample_articles():
    """Create a list of sample articles for testing."""
    now = dt.datetime.now(dt.timezone.utc)
    return [
        NewsItem(
            id="1",
            title="First Article",
            summary="Summary of first article",
            url="https://example.com/1",
            published=now - dt.timedelta(hours=1),
            source="BBC News"
        ),
        NewsItem(
            id="2",
            title="Second Article",
            summary="Summary of second article",
            url="https://example.com/2",
            published=now - dt.timedelta(hours=2),
            source="BBC News"
        ),
        NewsItem(
            id="3",
            title="Third Article with Special Keyword",
            summary="Summary of third article with test keyword",
            url="https://example.com/3",
            published=now - dt.timedelta(hours=3),
            source="BBC News"
        )
    ]

def test_get_all_news(news_service, sample_articles):
    """Test retrieving all news articles."""
    # Add sample articles
    for article in sample_articles:
        news_service.news_store.append(article)
    
    # Get all articles
    articles = news_service.get_all_news()
    
    # Verify results
    assert len(articles) == 3
    assert articles[0].id == "1"  # Should be sorted newest first
    assert articles[-1].id == "3"  # Oldest last

def test_get_latest_news(news_service, sample_articles):
    """Test retrieving latest N news articles."""
    # Add sample articles
    for article in sample_articles:
        news_service.news_store.append(article)
    
    # Test with default count
    latest = news_service.get_latest_news()
    assert len(latest) == 3
    assert latest[0].id == "1"  # Newest first
    
    # Test with custom count
    latest = news_service.get_latest_news(2)
    assert len(latest) == 2
    assert latest[0].id == "1"
    assert latest[1].id == "2"

def test_search_news(news_service, sample_articles):
    """Test searching news articles by keyword."""
    # Add sample articles
    for article in sample_articles:
        news_service.news_store.append(article)
    
    # Search in title
    results = news_service.search_news("Special")
    assert len(results) == 1
    assert results[0].id == "3"
    
    # Search in summary
    results = news_service.search_news("test keyword")
    assert len(results) == 1
    assert results[0].id == "3"
    
    # Search with no matches
    results = news_service.search_news("nonexistent")
    assert len(results) == 0

def test_get_feed_status(news_service, sample_articles):
    """Test getting feed status information."""
    # Add sample articles and setup state
    for article in sample_articles:
        news_service.news_store.append(article)
    
    news_service.feed_state.latest_hash = "test_hash"
    news_service.feed_state.last_fetch_time = dt.datetime.now(dt.timezone.utc)
    news_service.feed_state.seen_ids.update(["1", "2", "3"])
    
    status = news_service.get_feed_status()
    
    assert status["feed_url"] == settings.BBC_MIDDLE_EAST_RSS
    assert status["total_articles_stored"] == 3
    assert status["unique_articles_seen"] == 3
    assert status["latest_content_hash"] == "test_hash"
    assert status["latest_article"]["id"] == "1"
    assert not status["polling_active"]  # No active polling task

@pytest.mark.asyncio
async def test_polling_lifecycle(news_service):
    """Test starting and stopping the polling task."""
    # Start polling
    await news_service.start_polling()
    assert news_service._polling_task is not None
    assert not news_service._polling_task.done()
    
    # Stop polling
    await news_service.stop_polling()
    assert news_service._polling_task.done()
    
    # Start polling again
    await news_service.start_polling()
    assert not news_service._polling_task.done()
    await news_service.stop_polling()

@pytest.mark.asyncio
async def test_rss_poller_error_handling(news_service):
    """Test error handling in the RSS poller task."""
    with patch('services.news_service.fetch_feed', new_callable=AsyncMock) as mock_fetch:
        # Simulate fetch error
        mock_fetch.side_effect = Exception("Test error")
        
        # Start polling
        await news_service.start_polling()
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Stop polling
        await news_service.stop_polling()
        
        # Verify service remains operational
        assert len(news_service.news_store) == 0
        assert news_service.get_feed_status()["polling_active"] is False 