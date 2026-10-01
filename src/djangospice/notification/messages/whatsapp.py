from dataclasses import  dataclass
from .base import Message


@dataclass(slots=True, kw_only=True)
class WhatsAppMessage(Message):
    """
    Payload for WhatsApp Business API messaging.
    
    Attributes:
        body (str): The text content of the WhatsApp message.
        media (str | None): URL to media (image/video/document) to include.
        caption (str | None): Caption for the included media.
    """
    body: str = ""
    media: str | None = None
    caption: str | None = None

