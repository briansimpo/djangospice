from abc import ABC, abstractmethod
from functools import cached_property

from django.contrib.auth.models import AbstractUser

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


class BaseNotification(ABC):
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

    level: NotificationLevel = NotificationLevel.INFO
    category: str | None = None
    queue: str = "default"
    required: bool = False
    priority: int = 0

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @cached_property
    def type(self) -> str:
        """
        Fully-qualified notification type.

        Returns:
            str: The app path and class name (e.g., 'myapp.notifications.Alert').
        """
        return f"{self.__class__.__module__}.{self.__class__.__name__}"

    def channels(self, user: AbstractUser) -> tuple[Channel, ...]:
        """
        Define the default delivery channels for this notification.

        Args:
            user (AbstractUser): The recipient of the notification.

        Returns:
            tuple[Channel, ...]: A tuple of supported channels.
        """
        return (
            Channel.EMAIL,
            Channel.WEBSOCKET,
        )

    def supports(self, channel: Channel, user: AbstractUser) -> bool:
        """
        Check if the notification supports delivery via the specified channel.

        Args:
            channel (Channel): The channel to check.
            user (AbstractUser): The recipient of the notification.

        Returns:
            bool: True if the channel is supported, False otherwise.
        """
        return channel in self.channels(user)

    def to_message(self, channel: Channel, user: AbstractUser) -> Message | None:
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

    @abstractmethod
    def to_database(self, user: AbstractUser) -> DatabaseMessage:
        """
        Build a database message for in-app or persistent notifications.
        
        Must be implemented by subclasses.

        Args:
            user (AbstractUser): The recipient of the notification.

        Returns:
            DatabaseMessage: The constructed database message payload.
        """
        return NotImplementedError

    def to_email(self, user: AbstractUser) -> EmailMessage | None:
        """Build an email message payload."""
        return None

    def to_sms(self, user: AbstractUser) -> SmsMessage | None:
        """Build an SMS message payload."""
        return None

    def to_push(self, user: AbstractUser) -> PushMessage | None:
        """Build a mobile push notification payload."""
        return None

    def to_whatsapp(self, user: AbstractUser) -> WhatsAppMessage | None:
        """Build a WhatsApp message payload."""
        return None

    def to_slack(self, user: AbstractUser) -> SlackMessage | None:
        """Build a Slack message payload."""
        return None

    def to_discord(self, user: AbstractUser) -> DiscordMessage | None:
        """Build a Discord message payload."""
        return None

    def to_telegram(self, user: AbstractUser) -> TelegramMessage | None:
        """Build a Telegram message payload."""
        return None

    def __repr__(self) -> str:
        """Returns a string representation of the BaseNotification instance."""
        return (
            f"<{self.__class__.__name__} "
            f"type='{self.type}' "
            f"level='{self.level}'>"
        )
        