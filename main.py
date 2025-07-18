"""
FastAPI RSS News Fetcher for BBC Middle East News - Main Application

This is the main entry point for the application. It:
1. Creates the FastAPI app with proper configuration
2. Includes API routes
3. Manages application lifespan (startup/shutdown)
4. Starts/stops the RSS polling service

Usage:
    uvicorn main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import router
from core.config import settings
from services.news_service import news_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.
    
    Startup: Start the RSS polling service
    Shutdown: Stop the RSS polling service gracefully
    """
    # Startup
    print(f"[STARTUP] Starting {settings.API_TITLE}")
    await news_service.start_polling()
    
    yield  # Application runs here
    
    # Shutdown
    print(f"[SHUTDOWN] Stopping {settings.API_TITLE}")
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


# For debugging - can be removed in production
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
