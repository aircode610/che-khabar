import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

    # User Interest Configuration
    USER_INTEREST_PROMPT: str = "Iran and Israel war news"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    _model: Optional[SentenceTransformer] = None
    _user_interest_embedding: Optional[NDArray[np.float32]] = None

    # Telegram Configuration
    TELEGRAM_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    TELEGRAM_MESSAGE_TEMPLATE = {
        'TITLE': "*{title}*",
        'DATE': "📅 {date}",
        'SUMMARY': "{summary}",
        'SOURCE': "🔍 _{source}_",
        'LINK': "🔗 {url}"
    }

    @property
    def telegram_bot_token(self) -> str:
        """Get the Telegram bot token from environment variables."""
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        return token

    @property
    def telegram_chat_id(self) -> str:
        """Get the Telegram chat ID from environment variables."""
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id:
            raise ValueError("TELEGRAM_CHAT_ID not found in environment variables")
        return chat_id

    # Sentence Transformer Configuration
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the sentence transformer model."""
        if self._model is None:
            self._model = SentenceTransformer(self.EMBEDDING_MODEL_NAME)
        return self._model

    @property
    def user_interest_embedding(self) -> NDArray[np.float32]:
        """Get the embedding for the user interest prompt."""
        if self._user_interest_embedding is None:
            tensor = self.model.encode(self.USER_INTEREST_PROMPT)
            self._user_interest_embedding = np.array(tensor, dtype=np.float32)
        return self._user_interest_embedding

settings = Settings() 
