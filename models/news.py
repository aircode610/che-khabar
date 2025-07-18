"""
Data models for the RSS news fetcher application.

This module contains the core data structures used throughout the application:
- NewsItem: Represents a single news article
- FeedState: Tracks RSS feed state for efficient polling
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional, Set


@dataclass
class FeedState:
    """
    Cache for a single RSS/Atom feed to track changes efficiently.
    
    Uses HTTP caching headers (ETag/Last-Modified) to minimize bandwidth
    and server load when the feed hasn't changed.
    """
    
    etag: Optional[str] = None
    modified: Optional[str] = None  # RFC-822 string for Last-Modified header
    seen_ids: Set[str] = field(default_factory=set)


@dataclass
class NewsItem:
    """
    Represents a single news article from the RSS feed.
    
    Contains all relevant information about a news article including
    metadata for API serialization.
    """
    
    id: str
    title: str
    url: str
    published: dt.datetime
    summary: str
    source: str

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
            "source": self.source
        } 