from typing import Any

from django.contrib.auth.models import AbstractUser
from django.db import models

from .base import BaseNotification
from .models import Notification
from .enums import Channel
from .metadata import Metadata


class NotificationBuilder:
    """
    Responsible for shaping business data and persisting the 
    core Notification record to the database.
    """

    @classmethod
    def messages(cls,user: AbstractUser, notification: BaseNotification, channels: tuple[Channel, ...]) -> dict[str, dict[str, Any]]:
        """Construct the channel-specific serialized payloads."""
        messages = {}

        for channel in channels:
            message = notification.to_message(channel, user)
            if message is None:
                continue
            
            # Use .value to ensure the key is a string for JSON serialization
            messages[channel.value] = message.to_dict()

        return messages

    @classmethod
    def build(cls,user: AbstractUser, notification: BaseNotification, channels: tuple[Channel, ...], actor: models.Model | None = None, target: models.Model | None = None) -> Notification:
        """
        Map the domain notification into a database record and save it.
        """
        
        level = getattr(notification.level, "value", notification.level)
        
        message = notification.to_database(user)
        messages = cls.messages(user, notification, channels)

        metadata = Metadata(
            type=notification.type,
            category=notification.category,
            link=message.link,
            actions=message.actions,
            icon=message.icon,
            image=message.image,
            context=message.context,
            messages=messages,
        )

        return Notification.objects.create(
            recipient=user,
            actor=actor,
            target=target,
            verb=message.title,
            description=message.body,
            level=level,
            data=metadata.to_dict(),
        )
