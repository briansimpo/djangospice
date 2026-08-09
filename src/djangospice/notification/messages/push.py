from dataclasses import  dataclass
from .base import Message


@dataclass(slots=True, kw_only=True)
class PushMessage(Message):
    """
    Payload for constructing a mobile/web Push Notification (e.g., FCM/APNS).
    
    Attributes:
        title (str): The notification title.
        body (str): The notification message body.
        image (str | None): URL of an image to display in the push banner.
        icon (str | None): Name or URL of the app icon to display.
        sound (str | None): The sound file to play upon delivery (default is system alert).
        badge (int | None): The unread badge count to apply to the app icon.
        click_action (str | None): Deep-link or action intent triggered on click.
    """
    title: str
    body: str
    image: str | None = None
    icon: str | None = None
    sound: str | None = None
    badge: int | None = None
    click_action: str | None = None

