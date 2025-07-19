import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.routes import router
from services.news_service import news_service
from core.config import settings

# Configure service loggers
logging.basicConfig(
    level=logging.INFO,
    format=settings.LOG_FORMAT,
    datefmt=settings.LOG_DATE_FORMAT
)

logger = logging.getLogger(__name__)
logging.getLogger('services.rss_fetcher').setLevel(logging.INFO)
logging.getLogger('services.news_service').setLevel(logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.API_TITLE}")
    await news_service.start_polling()
    
    yield
    
    # Shutdown
    logger.info(f"Stopping {settings.API_TITLE}")
    await news_service.stop_polling()

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include API routes
app.include_router(router)

# For debugging
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
