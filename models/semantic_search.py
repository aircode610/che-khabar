from dataclasses import dataclass
from enum import Enum
from models.news import NewsItem


class MatchConfidence(Enum):
    VERY_STRONG = "Very Strong Match"
    STRONG = "Strong Match"
    POSSIBLE = "Possible Match"
    WEAK = "Weak Match"


@dataclass
class SemanticSearchResult:
    """Represents a single semantic search result with metadata."""
    news_item: NewsItem
    similarity_score: float
    confidence: MatchConfidence
    
    def to_dict(self) -> dict:
        return {
            "article": self.news_item.to_dict(),
            "similarity_score": float(self.similarity_score),
            "confidence": self.confidence.value
        } 
        