import logging
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Generic, TypeVar, get_args, get_origin

from django.contrib.auth.models import AbstractUser
from djangospice.notification.messages import Message
from djangospice.notification.enums import Channel
from djangospice.notification.models import Notification

T = TypeVar("T", bound=Message)

logger = logging.getLogger(__name__)


class NotificationChannel(ABC, Generic[T]):
    """
    Abstract base class for notification delivery channels.
    """

    channel: ClassVar[Channel]
    message_class: ClassVar[type[T]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Automatically infer `message_class` from the Generic type argument [T]
        when a developer subclasses NotificationChannel.
        """
        super().__init_subclass__(**kwargs)

        # Inspect the generic base classes (e.g., NotificationChannel[EmailMessage])
        for base in getattr(cls, "__orig_bases__", []):
            origin = get_origin(base) or base
            if origin is NotificationChannel:
                args = get_args(base)
                if args:
                    cls.message_class = args[0]
                    break

    def __init__(self, **options: Any) -> None:
        self.options = options

    @abstractmethod
    def send(self, user: AbstractUser, notification: Notification) -> dict[str, Any] | None:
        pass
    

    def message(self, notification: Notification) -> T | None:
        # Check by Enum string value, then fallback to Enum instance key
        data = notification.data.get("messages", {}).get(self.channel.value)

        if not data:
            data = notification.data.get("messages", {}).get(self.channel)

        if not data:
            return None

        # self.message_class is now automatically populated!
        return self.message_class.from_dict(data)

