from djangospice.core.payload import Payload
from djangospice.events import EventListener, listen

from .broadcast import broadcast_event
from .events import (    
    JobEvent,
    JobCompleted,
    JobFailed,
    JobProgressed,
    JobStarted,
)


@listen(JobStarted)
@listen(JobProgressed)
@listen(JobCompleted)
@listen(JobFailed)
class JobEventListener(EventListener):

    should_queue = True
    queue_name = "job-notifications"

    retry_on = (ConnectionResetError, TimeoutError)
    max_retries = 5
    retry_backoff = 30

    def handle(self, event: JobEvent) -> None:
        payload = Payload()

        if isinstance(event, JobProgressed):
            payload.set("message", event.message)
            payload.set("extra", event.extra)

        elif isinstance(event, JobCompleted):
            payload.set("result", event.result)

        elif isinstance(event, JobFailed):
            payload.set("error", event.error)

        broadcast_event(
            event=event,
            data=payload.to_dict(),
        )