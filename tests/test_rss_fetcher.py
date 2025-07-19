import datetime as dt
import pytest
import respx
from httpx import Response

from core.config import settings
from models.news import FeedState, NewsItem
from services.rss_fetcher import fetch_feed, generate_latest_hash

# Sample RSS feed response for testing
SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>BBC News - Middle East</title>
        <link>https://www.bbc.co.uk/news/</link>
        <description>BBC News - Middle East</description>
        <lastBuildDate>Wed, 13 Mar 2024 12:00:00 GMT</lastBuildDate>
        <item>
            <title>Test Article 1</title>
            <description>Summary of test article 1</description>
            <link>https://www.bbc.co.uk/news/article1</link>
            <guid>article1-guid</guid>
            <pubDate>Wed, 13 Mar 2024 12:00:00 GMT</pubDate>
        </item>
        <item>
            <title>Test Article 2</title>
            <description>Summary of test article 2</description>
            <link>https://www.bbc.co.uk/news/article2</link>
            <guid>article2-guid</guid>
            <pubDate>Wed, 13 Mar 2024 11:00:00 GMT</pubDate>
        </item>
    </channel>
</rss>"""

@pytest.fixture
def feed_state():
    """Create a fresh FeedState instance for each test."""
    return FeedState()

@pytest.mark.asyncio
async def test_fetch_feed_success(feed_state):
    """Test successful RSS feed fetch with new articles."""
    with respx.mock:
        # Mock the RSS feed endpoint
        respx.get(settings.BBC_MIDDLE_EAST_RSS).mock(
            return_value=Response(200, text=SAMPLE_RSS)
        )
        
        # Fetch feed
        articles = await fetch_feed(settings.BBC_MIDDLE_EAST_RSS, feed_state)
        
        # Verify results
        assert len(articles) == 2
        assert isinstance(articles[0], NewsItem)
        assert articles[0].title == "Test Article 1"
        assert articles[0].id == "article1-guid"
        assert articles[1].title == "Test Article 2"
        assert articles[1].id == "article2-guid"
        
        # Verify state updates
        assert len(feed_state.seen_ids) == 2
        assert feed_state.latest_hash is not None
        assert feed_state.last_fetch_time is not None

@pytest.mark.asyncio
async def test_fetch_feed_no_changes(feed_state):
    """Test feed fetch when content hasn't changed."""
    with respx.mock:
        # First fetch to populate state
        respx.get(settings.BBC_MIDDLE_EAST_RSS).mock(
            return_value=Response(200, text=SAMPLE_RSS)
        )
        await fetch_feed(settings.BBC_MIDDLE_EAST_RSS, feed_state)
        
        # Second fetch with same content
        articles = await fetch_feed(settings.BBC_MIDDLE_EAST_RSS, feed_state)
        assert len(articles) == 0  # No new articles

@pytest.mark.asyncio
async def test_fetch_feed_error_handling(feed_state):
    """Test error handling for various HTTP errors."""
    with respx.mock:
        # Test 404 response
        respx.get(settings.BBC_MIDDLE_EAST_RSS).mock(
            return_value=Response(404)
        )
        articles = await fetch_feed(settings.BBC_MIDDLE_EAST_RSS, feed_state)
        assert articles == []
        
        # Test timeout
        respx.get(settings.BBC_MIDDLE_EAST_RSS).mock(
            side_effect=TimeoutError
        )
        articles = await fetch_feed(settings.BBC_MIDDLE_EAST_RSS, feed_state)
        assert articles == []

@pytest.mark.asyncio
async def test_fetch_feed_invalid_date(feed_state):
    """Test handling of invalid publication dates."""
    invalid_date_rss = SAMPLE_RSS.replace(
        "Wed, 13 Mar 2024 12:00:00 GMT",
        "Invalid Date Format"
    )
    
    with respx.mock:
        respx.get(settings.BBC_MIDDLE_EAST_RSS).mock(
            return_value=Response(200, text=invalid_date_rss)
        )
        
        articles = await fetch_feed(settings.BBC_MIDDLE_EAST_RSS, feed_state)
        assert len(articles) == 2
        # Should use current time as fallback
        assert isinstance(articles[0].published, dt.datetime)

def test_generate_latest_hash():
    """Test hash generation for feed content."""
    import feedparser
    
    # Test with empty feed
    empty_feed = feedparser.parse("")
    assert generate_latest_hash(empty_feed) == ""
    
    # Test with sample feed
    feed = feedparser.parse(SAMPLE_RSS)
    hash1 = generate_latest_hash(feed)
    assert isinstance(hash1, str)
    assert len(hash1) == 40  # SHA-1 hash length 