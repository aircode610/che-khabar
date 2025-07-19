import logging
from telegram import Bot

from models.news import NewsItem
from core.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TelegramBot:
    def __init__(self, token: str | None = None, chat_id: str | None = None):
        """
        Initialize Telegram bot with token and chat ID.
        If not provided, will use values from environment variables.
        """
        self.token = token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id
        self.bot = Bot(token=self.token)
    
    def send_news(self, news_item: NewsItem):
        """Send a news item to Telegram."""
        try:
            message = self._format_message(news_item)
            result = self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"Sent news: {news_item.title}")
            return result
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
    
    def _format_message(self, news_item: NewsItem) -> str:
        """Format the news item as a message with Markdown."""
        def escape_markdown(text: str) -> str:
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')
            return text
        
        title = escape_markdown(news_item.title) if news_item.title else "No Title"
        date = news_item.published.strftime(settings.TELEGRAM_DATE_FORMAT) if news_item.published else "Unknown date"
        summary = escape_markdown(news_item.summary) if news_item.summary else "No summary provided."
        source = escape_markdown(news_item.source) if news_item.source else "Source unknown"
        url = news_item.url if news_item.url else ""
        
        message = (
            f"{settings.TELEGRAM_MESSAGE_TEMPLATE['TITLE'].format(title=title)}\n"
            f"{settings.TELEGRAM_MESSAGE_TEMPLATE['DATE'].format(date=date)}\n\n"
            f"{settings.TELEGRAM_MESSAGE_TEMPLATE['SUMMARY'].format(summary=summary)}\n\n"
            f"{settings.TELEGRAM_MESSAGE_TEMPLATE['SOURCE'].format(source=source)}\n"
            f"{settings.TELEGRAM_MESSAGE_TEMPLATE['LINK'].format(url=url)}"
        )
        return message

telegram_bot = TelegramBot()
