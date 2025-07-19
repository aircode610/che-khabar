import pytest
import numpy as np
from datetime import datetime, timezone
from models.news import NewsItem
from services.clustering_service import NewsClusteringService

@pytest.fixture
def clustering_service():
    """Create a fresh clustering service for each test."""
    return NewsClusteringService(cluster_threshold=2)  # Small threshold for testing

@pytest.fixture
def sample_embedded_articles():
    """Create sample articles with embeddings for testing."""
    now = datetime.now(timezone.utc)
    
    # Create two groups of similar articles
    war_articles = [
        NewsItem(
            id="war1",
            title="Israel-Gaza Conflict Updates",
            summary="Latest developments in the ongoing conflict",
            published=now,
            embedding=np.array([0.1, 0.2, 0.3] * 128, dtype=np.float32)  # 384-dim vector
        ),
        NewsItem(
            id="war2",
            title="Peace Talks in Middle East",
            summary="Negotiations for ceasefire continue",
            published=now,
            embedding=np.array([0.11, 0.21, 0.31] * 128, dtype=np.float32)  # Similar to war1
        )
    ]
    
    economy_articles = [
        NewsItem(
            id="econ1",
            title="Oil Prices Rise",
            summary="Global market impact on oil prices",
            published=now,
            embedding=np.array([0.8, 0.7, 0.6] * 128, dtype=np.float32)  # Different pattern
        ),
        NewsItem(
            id="econ2",
            title="Market Response to Crisis",
            summary="Economic implications of regional tensions",
            published=now,
            embedding=np.array([0.81, 0.71, 0.61] * 128, dtype=np.float32)  # Similar to econ1
        )
    ]
    
    return war_articles + economy_articles

def test_add_item(clustering_service, sample_embedded_articles):
    """Test adding items to clustering service."""
    # Add first item
    clustering_service.add_item(sample_embedded_articles[0].id, sample_embedded_articles[0])
    assert clustering_service.state.items_since_last_cluster == 1
    assert clustering_service.state.needs_clustering
    
    # Add second item - should trigger clustering threshold
    clustering_service.add_item(sample_embedded_articles[1].id, sample_embedded_articles[1])
    assert clustering_service.state.items_since_last_cluster == 2
    assert clustering_service.should_cluster()

def test_cluster_items(clustering_service, sample_embedded_articles):
    """Test clustering of items."""
    # Create dictionary of items
    items = {article.id: article for article in sample_embedded_articles}
    
    # Perform clustering
    clustering_service.cluster_items(items)
    
    # Check that items were clustered
    assert len(clustering_service.item_topics) == 4
    
    # Check that similar articles are in the same topic
    war1_topic = clustering_service.item_topics["war1"]
    war2_topic = clustering_service.item_topics["war2"]
    assert war1_topic == war2_topic
    
    econ1_topic = clustering_service.item_topics["econ1"]
    econ2_topic = clustering_service.item_topics["econ2"]
    assert econ1_topic == econ2_topic
    
    # War and economy articles should be in different topics
    assert war1_topic != econ1_topic

def test_get_topic_info(clustering_service, sample_embedded_articles):
    """Test retrieving topic information."""
    # First cluster the items
    items = {article.id: article for article in sample_embedded_articles}
    clustering_service.cluster_items(items)
    
    # Get topic ID for first article
    topic_id = clustering_service.item_topics["war1"]
    
    # Get topic info
    topic_info = clustering_service.get_topic_info(topic_id)
    
    assert topic_info is not None
    assert "topic_id" in topic_info
    assert "news_count" in topic_info
    assert "news_ids" in topic_info
    assert "keywords" in topic_info
    assert len(topic_info["news_ids"]) == 2  # Should have both war articles

def test_get_all_topics(clustering_service, sample_embedded_articles):
    """Test getting all topics."""
    # First cluster the items
    items = {article.id: article for article in sample_embedded_articles}
    clustering_service.cluster_items(items)
    
    # Get all topics
    topics = clustering_service.get_all_topics()
    
    assert len(topics) > 0  # Should have at least one topic
    
    # Each topic should have a list of news IDs
    for topic_id, news_ids in topics.items():
        assert isinstance(news_ids, list)
        assert len(news_ids) > 0

def test_get_all_topics_with_keywords(clustering_service, sample_embedded_articles):
    """Test getting all topics with their keywords."""
    # First cluster the items
    items = {article.id: article for article in sample_embedded_articles}
    clustering_service.cluster_items(items)
    
    # Get topics with keywords
    topics = clustering_service.get_all_topics_with_keywords()
    
    assert len(topics) > 0
    
    # Check structure of topic information
    for topic_id, topic_info in topics.items():
        assert "news_ids" in topic_info
        assert "keywords" in topic_info
        assert isinstance(topic_info["news_ids"], list)
        assert isinstance(topic_info["keywords"], list)

def test_error_handling(clustering_service):
    """Test error handling with invalid inputs."""
    # Try to add item without embedding
    article = NewsItem(
        id="invalid1",
        title="Invalid Article",
        summary="No embedding",
        published=datetime.now(timezone.utc),
        embedding=None
    )
    
    clustering_service.add_item(article.id, article)
    assert clustering_service.state.items_since_last_cluster == 0  # Should not count invalid items
    
    # Try to get info for non-existent topic
    topic_info = clustering_service.get_topic_info(999)
    assert topic_info is None 