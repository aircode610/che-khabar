"""
FastAPI routes for the news API.

This module defines all API endpoints for:
- Getting news articles
- Searching news
- Feed status and statistics
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from core.config import settings
from services.news_service import news_service

# Create API router
router = APIRouter()


@router.get("/")
async def read_root():
    """Root endpoint with basic API information."""
    return {
        "message": settings.API_TITLE,
        "status": "running",
        "feed_source": "BBC Middle East",
        "endpoints": {
            "all_news": "/news",
            "latest_news": "/news/latest/{count}",
            "search_news": "/news/search/{keyword}",
            "feed_status": "/news/status"
        }
    }


@router.get("/news")
async def get_all_news():
    """Get all stored news articles."""
    articles = news_service.get_all_news()
    return {
        "total_articles": len(articles),
        "articles": [item.to_dict() for item in articles]
    }


@router.get("/news/latest")
@router.get("/news/latest/{count}")
async def get_latest_news(count: int = 10):
    """
    Get the latest N news articles.
    
    Args:
        count: Number of articles to return (default: 10, max: 50)
    """
    if count <= 0:
        raise HTTPException(
            status_code=400, 
            detail="Count must be positive"
        )
    
    if count > 50:
        raise HTTPException(
            status_code=400,
            detail="Count cannot exceed 50"
        )
    
    latest_items = news_service.get_latest_news(count)
    
    return {
        "requested_count": count,
        "returned_count": len(latest_items),
        "articles": [item.to_dict() for item in latest_items]
    }


@router.get("/news/search/{keyword}")
async def search_news(keyword: str):
    """
    Search news articles by keyword in title or summary.
    
    Args:
        keyword: Search term to look for
    """
    if len(keyword.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="Search keyword must be at least 2 characters long"
        )
    
    matching_articles = news_service.search_news(keyword)
    
    return {
        "keyword": keyword,
        "total_matches": len(matching_articles),
        "articles": [item.to_dict() for item in matching_articles]
    }


@router.get("/news/status")
async def get_feed_status():
    """Get RSS feed polling status and statistics."""
    return news_service.get_feed_status()


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    feed_status = news_service.get_feed_status()
    
    return {
        "status": "healthy",
        "polling_active": feed_status["polling_active"],
        "articles_count": feed_status["total_articles_stored"],
        "timestamp": "2025-01-18T12:00:00Z"  # Would use actual timestamp in production
    } 