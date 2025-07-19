from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

from core.config import settings
from services.news_service import news_service

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
async def get_latest_news(count: int = settings.DEFAULT_ARTICLES_COUNT):
    """Get the latest N news articles."""
    if count <= 0:
        raise HTTPException(
            status_code=400, 
            detail="Count must be positive"
        )
    
    if count > settings.MAX_ARTICLES_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Count cannot exceed {settings.MAX_ARTICLES_PER_REQUEST}"
        )
    
    latest_items = news_service.get_latest_news(count)
    return {
        "requested_count": count,
        "returned_count": len(latest_items),
        "articles": [item.to_dict() for item in latest_items]
    }


@router.get("/news/search/{keyword}")
async def search_news(keyword: str):
    """Search news articles by keyword in title or summary."""
    if len(keyword.strip()) < settings.MIN_SEARCH_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Search keyword must be at least {settings.MIN_SEARCH_LENGTH} characters long"
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
    try:
        feed_status = news_service.get_feed_status()
        
        return {
            "status": "healthy",
            "polling_active": feed_status["polling_active"],
            "articles_count": feed_status["total_articles_stored"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        } 
    