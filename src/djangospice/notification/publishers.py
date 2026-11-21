from django.db import transaction

from .models import Notification
from .payload import payload

from djangospice.websocket.broadcast import Broadcast


def broadcast_event(event: str, notification: Notification) -> None:
    recipient_id = notification.recipient_id

    if not recipient_id:
        return

    Broadcast.event(
        event=event,
        user=recipient_id,
        data=notification.to_dict()
    )


def broadcast_read_all(recipient_id: str) -> None:
    if not recipient_id:
        return

    Broadcast.event(
        event="notification_read_all",
        user=recipient_id,
    )


def notification_created(notification: Notification) -> None:
    notification = payload(notification)

    transaction.on_commit(
        lambda: broadcast_event(
            event="notification_created",
            notification=notification,
        )
    )


def notification_read(notification: Notification) -> None:
    notification = payload(notification)

    transaction.on_commit(
        lambda: broadcast_event(
            event="notification_read",
            notification=notification,
        )
    )


def notification_unread(notification: Notification) -> None:
    notification = payload(notification)

    transaction.on_commit(
        lambda: broadcast_event(
            event="notification_unread",
            notification=notification,
        )
    )


def notification_deleted(notification: Notification) -> None:
    notification = payload(notification)

    transaction.on_commit(
        lambda: broadcast_event(
            event="notification_deleted",
            notification=notification,
        )
    )


def notification_read_all(recipient_id) -> None:
    transaction.on_commit(
        lambda: broadcast_read_all(recipient_id)
    )