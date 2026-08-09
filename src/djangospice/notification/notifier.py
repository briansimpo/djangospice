from typing import Any, Iterable
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.db.models import QuerySet

from djangospice.events import Event

from .base import BaseNotification
from .models import Notification
from .builder import NotificationBuilder
from .enums import Channel
from .events import NotificationRecordCreated
from .services import ChannelService, DeliveryService
from .celery import CeleryAdapter

User = get_user_model()

# Type aliases
UserType = AbstractUser | int | str
UserCollection = Iterable[UserType] | UserType | QuerySet[AbstractUser]


class Notifier:
    """
    Primary notification orchestration layer.

    Responsibilities:
        • Resolve recipients
        • Route channels via preferences
        • Delegate persistence to Builder
        • Queue deliveries
        • Dispatch domain events
    """

    @classmethod
    def resolve_users(cls, users: UserCollection) -> QuerySet[AbstractUser]:
        if not users:
            return User.objects.none()

        if isinstance(users, QuerySet):
            return users

        if not isinstance(users, (list, tuple, set)):
            users = [users]

        ids = [
            user.pk if hasattr(user, "pk") else user
            for user in users
        ]

        return User.objects.filter(pk__in=ids)

    @classmethod
    def create_deliveries(cls, notification: Notification, channels: tuple[Channel, ...]) -> list[Any]:
        deliveries = []
        
        celery = CeleryAdapter()

        for channel in channels:
            delivery = DeliveryService.create(
                notification=notification,
                channel=channel,
            )
            
            celery.dispatch(delivery.pk)
            
            deliveries.append(delivery)

        return deliveries

    @classmethod
    def send(cls, users: UserCollection, notification: BaseNotification, actor: models.Model | None = None, target: models.Model | None = None ) -> list[Notification]:
        
        users = cls.resolve_users(users)
        notifications = []

        with transaction.atomic():
            for user in users:
                
                # 1. Route
                channels = ChannelService.channels(
                    user=user,
                    notification=notification,
                )

                # 2. Build & Persist
                notification_record = NotificationBuilder.build(
                    user=user,
                    notification=notification,
                    channels=channels,
                    actor=actor,
                    target=target,
                )

                # 3. Deliver
                cls.create_deliveries(
                    notification_record,
                    channels,
                )
                
                Event.dispatch(NotificationRecordCreated(notification_record))

                notifications.append(notification_record)

               
        return notifications