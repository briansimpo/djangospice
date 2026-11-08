from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models, transaction

from .base import Notification
from .models import Notification as NotificationModel
from .models import NotificationAction


class NotificationBuilder:
    """
    Responsible for persisting notifications and their executable actions.
    """

    @staticmethod
    def _append_notification_id(url: str, notification_id: int) -> str:
        """Add or replace the notification ID in an action URL."""

        parts = urlsplit(url)

        query = [
            (key, value)
            for key, value in parse_qsl(
                parts.query,
                keep_blank_values=True,
            )
            if key != "notification_id"
        ]
        query.append(("notification_id", str(notification_id)))

        return urlunsplit((
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            parts.fragment,
        ))

    @staticmethod
    def _validate_actions(actions: list) -> None:
        """Ensure action names are unique within a notification."""

        seen = set()
        duplicates = set()

        for action in actions:
            if action.name in seen:
                duplicates.add(action.name)
            seen.add(action.name)

        if duplicates:
            raise ValidationError({
                "actions": (
                    "Duplicate notification action names: "
                    + ", ".join(sorted(duplicates))
                )
            })

    @classmethod
    @transaction.atomic
    def build(cls, user: AbstractUser, notification: Notification, actor: models.Model | None = None, target: models.Model | None = None) -> NotificationModel:
        """Persist a notification and its associated actions."""

        message = notification.to_database(user)

        actions = [
            *notification.get_actions(),
            *message.get_actions(),
        ]

        cls._validate_actions(actions)

        instance = NotificationModel.objects.create(
            recipient=user,
            actor=actor if actor is not None else user,
            target=target,
            verb=message.title,
            description=message.body,
            level=getattr(notification.level, "value", notification.level),
            data={
                "type": notification.type,
                "category": notification.category,
                "url": message.url,
                "icon": message.icon,
                "image": message.image,
                "context": message.context,
                "metadata": message.metadata,
            },
        )

        NotificationAction.objects.bulk_create([
            NotificationAction(
                notification=instance,
                key=f"{instance.pk}_{action.name}",
                name=action.name,
                url=cls._append_notification_id(
                    action.url,
                    instance.pk,
                ),
                label=action.label,
                icon=action.icon or "",
                method=action.method,
                style=action.style,
                status=action.status,
                attributes=action.attributes,
            )
            for action in actions
        ])

        return instance