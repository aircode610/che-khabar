from typing import List, Optional
import numpy as np
from sklearn.preprocessing import normalize
import logging
import re

from core.config import settings
from models.news import NewsItem
from models.semantic_search import MatchConfidence, SemanticSearchResult

logger = logging.getLogger(__name__)


class SemanticSearchService:
    TITLE_WEIGHT: float = 0.7
    SUMMARY_WEIGHT: float = 0.3
    EXACT_MATCH_BOOST: float = 0.3 

    def __init__(self):
        self.confidence_thresholds = {
            0.85: MatchConfidence.VERY_STRONG,
            0.7: MatchConfidence.STRONG,
            0.6: MatchConfidence.POSSIBLE,
            0.0: MatchConfidence.WEAK
        }
    
    def _calculate_exact_match_score(self, query: str, title: Optional[str], summary: Optional[str]) -> float:
        """Calculate exact match score based on word presence."""
        query_words = set(re.findall(r'\w+', query.lower()))
        title_words = set(re.findall(r'\w+', title.lower() if title else ""))
        summary_words = set(re.findall(r'\w+', summary.lower() if summary else ""))
        
        title_matches = len(query_words & title_words) / len(query_words) if query_words else 0
        summary_matches = len(query_words & summary_words) / len(query_words) if query_words else 0
        
        return (title_matches * self.TITLE_WEIGHT + summary_matches * self.SUMMARY_WEIGHT)
    
    def search(
        self,
        query: str,
        articles: List[NewsItem],
        min_threshold: float = 0.5,
        title_weight: Optional[float] = None,
        summary_weight: Optional[float] = None,
        max_results: int = 10
    ) -> List[SemanticSearchResult]:
        """
        Search articles using a combination of semantic similarity and exact word matching.
        """
        t_weight = title_weight if title_weight is not None else self.TITLE_WEIGHT
        s_weight = summary_weight if summary_weight is not None else self.SUMMARY_WEIGHT
        
        total_weight = t_weight + s_weight
        t_weight = t_weight / total_weight
        s_weight = s_weight / total_weight
        
        query_embedding = settings.model.encode(query)
        query_embedding = np.array(query_embedding)
        query_embedding = normalize(query_embedding.reshape(1, -1))[0]
        
        results: List[SemanticSearchResult] = []
        
        for item in articles:
            if item.embedding is None:
                continue
                
            article_embedding = np.array(item.embedding)
            article_embedding = normalize(article_embedding.reshape(1, -1))[0]
            semantic_similarity = np.dot(query_embedding, article_embedding)
            
            exact_match_score = self._calculate_exact_match_score(
                query, 
                item.title, 
                item.summary
            )
            
            combined_score = max(
                semantic_similarity,
                semantic_similarity + (exact_match_score * self.EXACT_MATCH_BOOST)
            )
            
            if combined_score >= min_threshold:
                confidence = next(
                    level for threshold, level in sorted(
                        self.confidence_thresholds.items(),
                        key=lambda x: x[0],
                        reverse=True
                    )
                    if combined_score >= threshold
                )
                
                results.append(SemanticSearchResult(
                    news_item=item,
                    similarity_score=combined_score,
                    confidence=confidence
                ))
                
                logger.info(
                    f"Match scores - Semantic: {semantic_similarity:.3f}, "
                    f"Exact: {exact_match_score:.3f}, Combined: {combined_score:.3f}\n"
                    f"Query: {query}\n"
                    f"Title: {item.title}\n"
                    f"Summary: {item.summary}\n"
                    f"---"
                )
        
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:max_results]


semantic_search_service = SemanticSearchService() 
