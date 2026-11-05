from __future__ import annotations

from typing import Iterable

from django.db import transaction

from djangospice.events import Event

from .events import (
    NotificationCreated,
    NotificationDeleted,
    NotificationRead,
    NotificationReadAll,
    NotificationUnread,
)
from .models import Notification
from .payload import payload



def serialize_notification(notification: Notification) -> dict:
    return payload(notification).to_dict()


def serialize_notifications(notifications: Iterable[Notification]) -> list[dict]:
    return [
        serialize_notification(notification)
        for notification in notifications
    ]


def notification_created(notification: Notification) -> None:
    notification = payload(notification)

    transaction.on_commit(
        lambda: Event.dispatch(
            NotificationCreated(
                notification=notification
            )
        )
    )


def notification_read(notification: Notification) -> None:
    notification = payload(notification)

    transaction.on_commit(
        lambda: Event.dispatch(
            NotificationRead(
                notification=notification,
            )
        )
    )



def notification_read_all(recipient) -> None:
    transaction.on_commit(
        lambda: Event.dispatch(
            NotificationReadAll(recipient=recipient)
        )
    )



def notification_unread(notification: Notification) -> None:
    notification = payload(notification)

    transaction.on_commit(
        lambda: Event.dispatch(
            NotificationUnread(
                notification=notification,
            )
        )
    )


def notification_deleted(notification: Notification) -> None:
    notification = payload(notification)

    transaction.on_commit(
        lambda: Event.dispatch(
            NotificationDeleted(
                notification=notification,
            )
        )
    )