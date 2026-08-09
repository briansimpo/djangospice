
from djangospice.events import EventListener, listen
from .broadcast import NotificationBroadcast
from .events import NotificationRecordCreated


@listen(NotificationRecordCreated)
class NotificationBroadcastListener(EventListener):

    should_queue = True
    queue_name = "broadcast-notifications"

    retry_on = (ConnectionResetError, TimeoutError)
    max_retries = 5
    retry_backoff = 30 

    def handle(self, event: NotificationRecordCreated) -> None:
        NotificationBroadcast.broadcast(event.notification)