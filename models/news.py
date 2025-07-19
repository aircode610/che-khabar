import datetime as dt
from dataclasses import dataclass, field
from typing import Optional, Set
import numpy as np
from numpy.typing import NDArray


@dataclass
class FeedState:
    """
    Cache for a single RSS/Atom feed to track changes efficiently.
    
    Tracks:
    - Content hash of latest article
    - Last successful fetch time
    - Set of seen article IDs to prevent duplicates
    """
    
    latest_hash: Optional[str] = None 
    last_fetch_time: Optional[dt.datetime] = None
    seen_ids: Set[str] = field(default_factory=set)


@dataclass
class NewsItem:
    """
    Represents a single news article from the RSS feed.
    
    Contains all relevant information about a news article including
    metadata for API serialization and sentence transformer embeddings 
    for semantic similarity matching.
    """
    
    id: str
    published: dt.datetime
    title: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    source: Optional[str] = None
    embedding: Optional[NDArray[np.float32]] = None

    def to_dict(self) -> dict:
        """
        Convert NewsItem to dictionary for JSON serialization.
        
        Returns:
            dict: JSON-serializable dictionary representation
        """
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "published": self.published.isoformat(),
            "summary": self.summary,
            "source": self.source,
            "embedding": self.embedding.tolist() if self.embedding is not None else None
        } 
