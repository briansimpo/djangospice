from typing import Any
from dataclasses import  dataclass
from .base import Message


@dataclass(slots=True, kw_only=True)
class TelegramMessage(Message):
    """
    Payload for Telegram Bot API.
    
    Attributes:
        text (str): The text of the message.
        parse_mode (str | None): Parsing mode for text formatting (e.g., 'HTML' or 'MarkdownV2').
        disable_notification (bool): Sends the message silently (no sound).
        disable_web_page_preview (bool): Disables link previews for URLs in the message.
        reply_markup (dict[str, Any] | None): Inline keyboard or custom reply formats.
    """
    text: str = ""
    parse_mode: str | None = "HTML"
    disable_notification: bool = False
    disable_web_page_preview: bool = False
    reply_markup: dict[str, Any] | None = None