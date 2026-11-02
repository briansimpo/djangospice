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

def get_unread_notification_count(user):
    if user is not None:
        notifications = user.notifications.unread()
        return notifications.count()
    return 0


def dispatch_notification_created(notification: Notification, user=None) -> None:
    notification = payload(notification)
    unread_count = get_unread_notification_count(user)

    transaction.on_commit(
        lambda: Event.dispatch(
            NotificationCreated(
                notification=notification,
                unread_count=unread_count
            )
        )
    )


def dispatch_notification_read(notification: Notification, user=None) -> None:
    notification = payload(notification)
    unread_count = get_unread_notification_count(user)

    transaction.on_commit(
        lambda: Event.dispatch(
            NotificationRead(
                notification=notification,
                unread_count=unread_count
            )
        )
    )



def dispatch_notification_read_all(user=None) -> None:
    unread_count = get_unread_notification_count(user)
    
    transaction.on_commit(
        lambda: Event.dispatch(
            NotificationReadAll(
                unread_count=unread_count
            )
        )
    )



def dispatch_notification_unread(notification: Notification, user=None) -> None:
    notification = payload(notification)
    unread_count = get_unread_notification_count(user)

    transaction.on_commit(
        lambda: Event.dispatch(
            NotificationUnread(
                notification=notification,
                unread_count=unread_count
            )
        )
    )


def dispatch_notification_deleted(notification: Notification) -> None:
    notification = payload(notification)

    transaction.on_commit(
        lambda: Event.dispatch(
            NotificationDeleted(
                notification=notification,
            )
        )
    )