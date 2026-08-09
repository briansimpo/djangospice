from typing import Any
from dataclasses import  dataclass, field
from .base import Message


@dataclass(slots=True, kw_only=True)
class SlackMessage(Message):
    """
    Payload for Slack webhooks or Bot API.
    
    Attributes:
        text (str): Fallback text or simple message text.
        blocks (list[dict[str, Any]]): Slack Block Kit UI blocks for rich formatting.
        attachments (list[dict[str, Any]]): Legacy Slack attachments.
    """
    text: str = ""
    blocks: list[dict[str, Any]] = field(default_factory=list)
    attachments: list[dict[str, Any]] = field(default_factory=list)

