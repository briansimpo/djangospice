from djangospice.events import EventListener, listen
from djangospice.realtime import Broadcast

from .events import (
    NotificationEvent,
    NotificationCreated,
    NotificationRead,
    NotificationUnread,
    NotificationDeleted,
)


@listen(NotificationCreated)
@listen(NotificationRead)
@listen(NotificationUnread)
@listen(NotificationDeleted)
class NotificationEventListener(EventListener):

    should_queue = True
    queue_name = "broadcast-notifications"

    retry_on = (ConnectionResetError, TimeoutError)
    max_retries = 5
    retry_backoff = 30

    def handle(self, event: NotificationEvent) -> None:
        Broadcast.user(
            user=event.payload.recipient_id,
            data={
                "type": event.name,
                "notification": event.payload.to_dict(),
            },
        )