from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
from bertopic import BERTopic
from threading import Lock
import logging
from models.news import NewsItem

logger = logging.getLogger(__name__)

@dataclass
class ClusteringState:
    """Tracks the state of clustering operations"""
    last_cluster_time: Optional[float] = None
    items_since_last_cluster: int = 0
    needs_clustering: bool = False

class NewsClusteringService:
    def __init__(self, cluster_threshold: int = 5):
        self.lock = Lock()
        self.topic_model = BERTopic(
            min_topic_size=2,  # Small size since news trickles in
            verbose=True
        )
        # Store topic assignments: news_id -> topic_id
        self.item_topics: Dict[str, int] = {}
        # Track clustering state
        self.state = ClusteringState()
        # Configure when to cluster
        self.CLUSTER_THRESHOLD = cluster_threshold
    
    def should_cluster(self) -> bool:
        """Decide if we should run clustering"""
        return (
            self.state.needs_clustering and 
            self.state.items_since_last_cluster >= self.CLUSTER_THRESHOLD
        )
    
    def add_item(self, item_id: str, item: NewsItem) -> None:
        """Add a new item to be clustered"""
        with self.lock:
            if item.embedding is None:
                logger.warning(f"Item {item_id} has no embedding, skipping")
                return
            
            # Mark that we have new items
            self.state.needs_clustering = True
            self.state.items_since_last_cluster += 1
    
    def cluster_items(self, items: Dict[str, NewsItem]) -> None:
        """Run clustering on provided items"""
        with self.lock:
            # Get all embeddings
            embeddings = []
            ids = []
            texts = []
            
            for id_, item in items.items():
                if item.embedding is not None:
                    try:
                        # Validate embedding shape and values
                        if not isinstance(item.embedding, np.ndarray):
                            logger.error(f"Invalid embedding type for item {id_}: {type(item.embedding)}")
                            continue
                        if np.isnan(item.embedding).any():
                            logger.error(f"NaN values in embedding for item {id_}")
                            continue
                        
                        embeddings.append(item.embedding)
                        ids.append(id_)
                        texts.append(f"{item.title or ''} {item.summary or ''}")
                    except Exception as e:
                        logger.error(f"Error processing item {id_}: {e}")
                        continue
            
            if not embeddings:
                logger.warning("No valid items with embeddings to cluster")
                return
            
            if len(embeddings) < self.CLUSTER_THRESHOLD:
                logger.info(f"Only {len(embeddings)} items, waiting for more before clustering")
                return
            
            # Convert to numpy array
            try:
                embeddings_array = np.array(embeddings)
                if embeddings_array.shape[1] != 384:  # Standard dimension for 'all-MiniLM-L6-v2'
                    logger.error(f"Invalid embedding dimension: {embeddings_array.shape[1]}, expected 384")
                    return
            except Exception as e:
                logger.error(f"Error creating embeddings array: {e}")
                return
            
            try:
                # Run clustering
                topics, _ = self.topic_model.fit_transform(
                    texts,
                    embeddings=embeddings_array
                )
                
                # Store topic assignments
                for id_, topic in zip(ids, topics):
                    self.item_topics[id_] = topic
                
                # Reset state
                self.state.needs_clustering = False
                self.state.items_since_last_cluster = 0
                
                # Log clustering results
                topic_counts = {}
                for topic in topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
                
                logger.info(f"Clustering complete:")
                logger.info(f"- Total items: {len(ids)}")
                logger.info(f"- Unique topics: {len(set(topics))}")
                logger.info(f"- Topic distribution: {topic_counts}")
                logger.info(f"- Outliers (topic -1): {topic_counts.get(-1, 0)}")
                
            except ValueError as e:
                logger.error(f"ValueError during clustering: {e}")
                logger.error("This might be due to invalid text content or embedding dimensions")
            except MemoryError as e:
                logger.error(f"MemoryError during clustering: {e}")
                logger.error("Not enough memory to perform clustering. Try reducing batch size")
            except Exception as e:
                logger.error(f"Unexpected error during clustering: {e}")
                logger.error("Stack trace:", exc_info=True)
    
    def get_all_topics(self) -> Dict[int, List[str]]:
        """Return all topic IDs mapped to their news IDs"""
        with self.lock:
            topic_to_news_ids: Dict[int, List[str]] = {}
            
            for news_id, topic_id in self.item_topics.items():
                if topic_id not in topic_to_news_ids:
                    topic_to_news_ids[topic_id] = []
                topic_to_news_ids[topic_id].append(news_id)
            
            return topic_to_news_ids
    
    def get_all_topics_with_keywords(self) -> Dict[int, dict]:
        """Return all topic IDs mapped to news IDs and their keywords"""
        with self.lock:
            topic_summary = {}
            
            for news_id, topic_id in self.item_topics.items():
                if topic_id not in topic_summary:
                    keywords = self.topic_model.get_topic(topic_id) if topic_id != -1 else []
                    topic_summary[topic_id] = {
                        "news_ids": [],
                        "keywords": [
                            {"word": word, "score": float(score)}
                            for word, score in keywords
                        ] if keywords else []
                    }
                topic_summary[topic_id]["news_ids"].append(news_id)
            
            return topic_summary
    
    def get_topic_info(self, topic_id: int) -> Optional[dict]:
        """Get detailed information about a specific topic"""
        with self.lock:
            if topic_id not in set(self.item_topics.values()):
                return None
            
            news_ids = [
                news_id for news_id, tid 
                in self.item_topics.items() 
                if tid == topic_id
            ]
            
            keywords = self.topic_model.get_topic(topic_id) if topic_id != -1 else []
            
            return {
                "topic_id": topic_id,
                "news_count": len(news_ids),
                "news_ids": news_ids,
                "keywords": [
                    {"word": word, "score": float(score)}
                    for word, score in keywords
                ] if keywords else []
            } 