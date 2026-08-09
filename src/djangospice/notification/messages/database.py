from dataclasses import  dataclass, field
from djangospice.notification.dataclass import NotificationAction, NotificationIntent
from .base import Message


@dataclass(slots=True, kw_only=True)
class DatabaseMessage(Message):
    """
    Message stored directly in the database (e.g., via django-notifications-hq).
    Used primarily for persistent, in-app notification centers.
    
    Attributes:
        title (str): The brief summary or title of the notification.
        body (str): The detailed text of the notification.
        icon (str | None): URL or identifier for an associated icon.
        action (str | None): URL or deep-link for when the notification is clicked.
        image (str | None): URL for a rich media image.
    """
    title: str
    body: str
    icon: str | None = None
    image: str | None = None
    # Executed when the notification itself is clicked.
    intent: NotificationIntent | None = None
    # Optional actions rendered by the client.
    actions: list[NotificationAction] = field(default_factory=list)

