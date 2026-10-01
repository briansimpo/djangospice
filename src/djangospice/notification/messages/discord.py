from typing import Any
from dataclasses import  dataclass, field
from .base import Message


@dataclass(slots=True, kw_only=True)
class DiscordMessage(Message):
    """
    Payload for Discord webhooks or Bot API.
    
    Attributes:
        content (str): The raw message text (supports basic Markdown).
        embeds (list[dict[str, Any]]): Rich embed objects.
        username (str | None): Override the default bot/webhook username.
        avatar_url (str | None): Override the default bot/webhook avatar.
    """
    content: str = ""
    embeds: list[dict[str, Any]] = field(default_factory=list)
    username: str | None = None
    avatar_url: str | None = None
