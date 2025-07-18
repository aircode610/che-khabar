"""
Configuration settings for the RSS news fetcher application.

This module contains all configurable parameters and settings used
throughout the application.
"""

from typing import List


class Settings:
    """Application configuration settings."""
    
    # RSS Feed Configuration
    BBC_MIDDLE_EAST_RSS: str = "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml"
    
    # Polling Configuration
    POLL_INTERVAL_SECONDS: int = 60
    REQUEST_TIMEOUT_SECONDS: int = 10
    
    # Storage Configuration
    MAX_STORED_ARTICLES: int = 100
    
    # API Configuration
    API_TITLE: str = "Che Khabar - BBC Middle East News API"
    API_DESCRIPTION: str = "RSS feed aggregator for BBC Middle East news"
    API_VERSION: str = "1.0.0"
    
    # Logging Configuration
    LOG_FORMAT: str = "[{time:%H:%M:%S}] {message}"


# Global settings instance
settings = Settings() 