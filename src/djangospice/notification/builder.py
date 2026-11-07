from typing import Any

from django.contrib.auth.models import AbstractUser
from django.db import models

from .base import Notification
from .models import Notification as NotificationModel

    
class NotificationBuilder:
    """
    Responsible for shaping business data and persisting the 
    core Notification record to the database.
    """

    @classmethod
    def build(cls, user: AbstractUser, notification: Notification, actor: models.Model | None = None, target: models.Model | None = None) -> Notification:
        """
        Map the domain notification into a database record and save it.
        """
        
        level = getattr(notification.level, "value", notification.level)
        
        message = notification.to_database(user)
        actions = notification.get_actions()
        actions.extend(message.get_actions())

        data = {
            "type": notification.type,
            "category": notification.category,
            "url": message.url,
            "icon": message.icon,
            "image": message.image,
            "context": message.context,
            "metadata": message.metadata,
            "actions": actions
        }

        return NotificationModel.objects.create(
            recipient=user,
            actor=actor or user,
            target=target,
            verb=message.title,
            description=message.body,
            level=level,
            data=data,
        )
