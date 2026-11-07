from functools import cached_property
from typing import Any

from django.http import HttpRequest
from djangospice.core.object import Object
from djangospice.core.executable import Executable
from djangospice.utils import safe_reverse

from .enums import (
    Channel,
    NotificationLevel,
)
from .messages import (
    DatabaseMessage,
    DiscordMessage,
    EmailMessage,
    Message,
    PushMessage,
    SlackMessage,
    SmsMessage,
    TelegramMessage,
    WhatsAppMessage,
)



class Notification(Executable, Object):
    """
    Base business notification.

    A notification represents a business event and is responsible
    for building channel-specific messages. Delivery, persistence, 
    and retries are handled by the framework.

    Attributes:
        level (NotificationLevel): The severity/level of the notification.
        category (str | None): Optional grouping category for notifications.
        queue (str): The Celery/task queue name for routing delivery.
        required (bool): Whether this notification bypasses user opt-out preferences.
        priority (int): Delivery priority (higher numbers indicate higher priority).
    """
    suffix = "Notification"
    level: NotificationLevel = NotificationLevel.INFO
    category: str | None = None
    queue: str = "default"
    required: bool = True
    priority: int = 0

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, request=request, **kwargs)


    @cached_property
    def type(self) -> str:
        """
        Fully-qualified notification type.

        Returns:
            str: The app path and class name (e.g., 'myapp.notifications.Alert').
        """
        return f"{self.__class__.__module__}.{self.__class__.__name__}"

    def channels(self, user) -> tuple[Channel, ...]:
        """
        Define the default delivery channels for this notification.

        Args:
            user (AbstractUser): The recipient of the notification.

        Returns:
            tuple[Channel, ...]: A tuple of supported channels.
        """
        return (
            Channel.EMAIL,
        )

    def supports(self, channel: Channel, user) -> bool:
        """
        Check if the notification supports delivery via the specified channel.

        Args:
            channel (Channel): The channel to check.
            user (AbstractUser): The recipient of the notification.

        Returns:
            bool: True if the channel is supported, False otherwise.
        """
        return channel in self.channels(user)

    def to_message(self, channel: Channel, user) -> Message | None:
        """
        Dynamically route to the correct message builder based on the channel.

        Args:
            channel (Channel): The target delivery channel.
            user (AbstractUser): The recipient of the notification.

        Returns:
            Message | None: The constructed message object if supported, otherwise None.
        """
        method_name = f"to_{channel.value}"
        method = getattr(self, method_name, None)
        
        # Ensure the attribute actually exists and is a method before calling
        if method and callable(method):
            return method(user)
            
        return None

    # ------------------------------------------------------------------
    # Channel-specific builders
    # ------------------------------------------------------------------

    def to_database(self, user) -> DatabaseMessage:
        """
        Build a database message for in-app or persistent notifications.
        
        Must be implemented by subclasses.

        Args:
            user (AbstractUser): The recipient of the notification.

        Returns:
            DatabaseMessage: The constructed database message payload.
        """
        return None

    def to_email(self, user) -> EmailMessage | None:
        """Build an email message payload."""
        return None

    def to_sms(self, user) -> SmsMessage | None:
        """Build an SMS message payload."""
        return None

    def to_push(self, user) -> PushMessage | None:
        """Build a mobile push notification payload."""
        return None

    def to_whatsapp(self, user) -> WhatsAppMessage | None:
        """Build a WhatsApp message payload."""
        return None

    def to_slack(self, user) -> SlackMessage | None:
        """Build a Slack message payload."""
        return None

    def to_discord(self, user) -> DiscordMessage | None:
        """Build a Discord message payload."""
        return None

    def to_telegram(self, user) -> TelegramMessage | None:
        """Build a Telegram message payload."""
        return None

    def dispatch_url(self):
        from .apps import namespace
        return safe_reverse(
            view_name="notification_action",
            namespace=namespace,
            kwargs={
                "app_name": self.identity.app_name,
                "class_name": self.identity.class_name,
            },
        )

    # ------------------------------------------------------------------
    # Notification actions
    # ------------------------------------------------------------------

    def _action_metadata(self, name: str) -> dict[str, Any]:
        """
        Return presentation metadata for an action.
        """

        method = self.get_method(name)

        if method is None:
            return {}

        metadata = method.get_metadata()
        
        return {
            "name": name,
            "label": metadata.get("label", name.replace("_", " ").title()),
            "method": method.method,
            "url":self.get_method_url(name),
            "style": "primary",
        }

    def get_actions(self) -> list[dict[str, Any]]:
        """
        Return action definitions suitable for serialization
        and rendering in notification interfaces.
        """

        return [
            self._action_metadata(name)
            for name in self.get_methods()
        ]