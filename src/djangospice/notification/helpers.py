from __future__ import annotations

from typing import Iterable

from django.db import transaction

from djangospice.events import Event

from .events import (
    NotificationCreated,
    NotificationDeleted,
    NotificationRead,
    NotificationUnread,
)
from .models import Notification
from .payload import NotificationPayload


def notification_payload(notification: Notification) -> NotificationPayload:
    return NotificationPayload.from_model(notification)


def serialize_notification(notification: Notification) -> dict:
    return notification_payload(notification).to_dict()


def serialize_notifications(notifications: Iterable[Notification]) -> list[dict]:
    return [
        serialize_notification(notification)
        for notification in notifications
    ]


def dispatch_notification_created(notification: Notification) -> None:
    payload = notification_payload(notification)

    transaction.on_commit(
        lambda: Event.dispatch(
            NotificationCreated(
                payload=payload,
            )
        )
    )


def dispatch_notification_read(notification: Notification) -> None:
    payload = notification_payload(notification)

    transaction.on_commit(
        lambda: Event.dispatch(
            NotificationRead(
                payload=payload,
            )
        )
    )


def dispatch_notification_unread(notification: Notification) -> None:
    payload = notification_payload(notification)

    transaction.on_commit(
        lambda: Event.dispatch(
            NotificationUnread(
                payload=payload,
            )
        )
    )


def dispatch_notification_deleted(notification: Notification) -> None:
    payload = notification_payload(notification)

    transaction.on_commit(
        lambda: Event.dispatch(
            NotificationDeleted(
                payload=payload,
            )
        )
    )