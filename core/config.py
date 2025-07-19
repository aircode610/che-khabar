class Settings:
    """Application configuration settings."""
    
    # RSS Feed Configuration
    BBC_MIDDLE_EAST_RSS: str = "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml"

    # Polling Configuration
    POLL_INTERVAL_SECONDS: int = 20
    REQUEST_TIMEOUT_SECONDS: int = 10
    
    # Storage Configuration
    MAX_STORED_ARTICLES: int = 100
    
    # API Configuration
    API_TITLE: str = "Che Khabar - BBC Middle East News API"
    API_DESCRIPTION: str = "RSS feed aggregator for BBC Middle East news"
    API_VERSION: str = "1.0.0"
    MIN_SEARCH_LENGTH: int = 2
    MAX_ARTICLES_PER_REQUEST: int = 50
    DEFAULT_ARTICLES_COUNT: int = 10
    
    # Logging Configuration
    LOG_FORMAT: str = "[%(asctime)s] %(message)s"
    LOG_DATE_FORMAT: str = "%H:%M:%S"

settings = Settings() 
