
from dataclasses import  dataclass
from .base import Message


@dataclass(slots=True, kw_only=True)
class SmsMessage(Message):
    """
    Payload for constructing an SMS message.
    
    Attributes:
        body (str): The text content of the SMS.
        sender (str | None): The alphanumeric sender ID or origin phone number.
    """
    body: str
    sender: str | None = None

