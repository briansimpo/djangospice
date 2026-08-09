from typing import Any
from dataclasses import  dataclass, field
from djangospice.core.payload import Payload
from .base import Message


@dataclass(slots=True, kw_only=True)
class EmailMessage(Message):
    """
    Payload for constructing an email delivery.
    
    Attributes:
        subject (str): The email subject line.
        text (str): The plain-text body of the email.
        html (str | None): The HTML body of the email.
        from_email (str | None): Custom sender address (overrides default).
        reply_to (list[str]): List of reply-to addresses.
        cc (list[str]): List of carbon-copy addresses.
        bcc (list[str]): List of blind carbon-copy addresses.
        attachments (list[Any]): List of file attachments.
        headers (dict[str, str]): Custom email headers.
    """
    subject: str
    text: str
    html: str | None = None
    from_email: str | None = None
    reply_to: list[str] = field(default_factory=list)
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    attachments: list[Any] = field(default_factory=list)
    headers: Payload= field(default_factory=Payload)

