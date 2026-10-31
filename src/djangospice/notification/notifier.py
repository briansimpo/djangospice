from typing import Any, Callable, Iterable

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.db.models import QuerySet

from .base import BaseNotification
from .models import Notification, NotificationDelivery
from .builder import NotificationBuilder
from .enums import Channel
from .services import ChannelService
from .celery import CeleryAdapter
from .helpers import dispatch_notification_created


# Type aliases
UserType = AbstractUser | int | str
UserCollection = Iterable[UserType] | UserType | QuerySet[AbstractUser]

NotificationFactory = Callable[[], BaseNotification]

NotificationInput = (
    BaseNotification
    | type[BaseNotification]
    | NotificationFactory
)


class Notifier:
    """
    Primary notification orchestration layer.

    Responsibilities:
        • Resolve recipients
        • Resolve notification instances
        • Route channels via preferences
        • Delegate persistence to Builder
        • Queue deliveries
        • Dispatch domain events
    """

    @classmethod
    def resolve_users(cls, users: UserCollection) -> QuerySet[AbstractUser]:
        User = get_user_model()
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
    def resolve_notification(cls, notification: NotificationInput, notification_kwargs: dict[str, Any] | None = None) -> BaseNotification:
        """
        Resolve a notification instance from an instance, class, or factory.
        """
        kwargs = notification_kwargs or {}

        # Already instantiated
        if isinstance(notification, BaseNotification):
            if kwargs:
                raise TypeError(
                    "notification_kwargs cannot be used with "
                    "a notification instance."
                )

            return notification

        # Notification class
        if isinstance(notification, type) and issubclass(
            notification, BaseNotification
        ):
            return notification(**kwargs)

        # Factory
        if callable(notification):
            if kwargs:
                raise TypeError(
                    "notification_kwargs cannot be used with "
                    "a notification factory. Pass arguments to the factory."
                )

            instance = notification()

            if not isinstance(instance, BaseNotification):
                raise TypeError(
                    "Notification factory must return a "
                    "BaseNotification instance."
                )

            return instance

        raise TypeError(
            "notification must be a BaseNotification instance, "
            "BaseNotification subclass, or factory."
        )

    @classmethod
    def create_deliveries(cls, notification: Notification, channels: tuple[Channel, ...]) -> list[Any]:

        deliveries = []
        celery = CeleryAdapter()

        for channel in channels:
            delivery = NotificationDelivery.objects.create(
                notification=notification,
                channel=channel,
            )

            celery.dispatch(str(delivery.pk))

            deliveries.append(delivery)

        return deliveries

    @classmethod
    def send(cls, users: UserCollection, notification: NotificationInput, actor: models.Model | None = None,  target: models.Model | None = None, notification_kwargs: dict[str, Any] | None = None) -> list[Notification]:

        # 1. Resolve notification
        notification = cls.resolve_notification(
            notification,
            notification_kwargs=notification_kwargs,
        )

        # 2. Resolve recipients
        users = cls.resolve_users(users)
        notifications = []

        with transaction.atomic():
            for user in users:

                # 3. Route
                channels = ChannelService.channels(
                    user=user,
                    notification=notification,
                )

                # 4. Build & Persist
                notification_record = NotificationBuilder.build(
                    user=user,
                    notification=notification,
                    channels=channels,
                    actor=actor,
                    target=target,
                )

                # 5. Deliver
                cls.create_deliveries(notification_record, channels)

                # 6. Dispatch event
                dispatch_notification_created(notification_record)

                notifications.append(notification_record)

        return notifications
