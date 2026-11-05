from djangospice.events import EventListener, listen
from djangospice.websocket import Broadcast

from .events import (
    NotificationEvent,
    NotificationCreated,
    NotificationRead,
    NotificationUnread,
    NotificationDeleted,
    NotificationReadAll,
)


@listen(NotificationCreated)
@listen(NotificationRead)
@listen(NotificationUnread)
@listen(NotificationDeleted)
class NotificationEventListener(EventListener):
    queue_name = "broadcast-notifications"

    retry_on = (ConnectionResetError, TimeoutError)
    max_retries = 5
    retry_backoff = 30

    def handle(self, event: NotificationEvent) -> None:
        recipient_id = event.notification.recipient_id

        Broadcast.event(
            event=event.name,
            user=recipient_id,
            data=event.notification.to_dict()
        )


@listen(NotificationReadAll)
class NotificationsEventListener(EventListener):
    queue_name = "broadcast-notifications"

    retry_on = (ConnectionResetError, TimeoutError)
    max_retries = 5
    retry_backoff = 30

    def handle(self, event: NotificationReadAll) -> None:
        recipient = event.recipient

        Broadcast.event(
            event=event.name,
            user=recipient,
        )
