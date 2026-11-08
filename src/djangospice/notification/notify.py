from __future__ import annotations

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
            NotificationReadAll(recipient)
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