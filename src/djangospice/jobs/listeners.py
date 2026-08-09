
from djangospice.events import BaseEvent, EventListener, listen
from .broadcast import broadcast_job_event
from .events import (
    JobStartedEvent,
    JobProgressedEvent,
    JobCompletedEvent,
    JobFailedEvent,
)


@listen(JobStartedEvent)
@listen(JobProgressedEvent)
@listen(JobCompletedEvent)
@listen(JobFailedEvent)
class JobBroadcastListener(EventListener):

    should_queue = True
    queue_name = "job-notifications"

    retry_on = (ConnectionResetError, TimeoutError)
    max_retries = 5
    retry_backoff = 30 


    def handle(self, event: BaseEvent) -> None:
        if isinstance(event, JobStartedEvent):
            broadcast_job_event(event.job, "STARTED")

        elif isinstance(event, JobProgressedEvent):
            broadcast_job_event(
                event.job, 
                "PROGRESS", 
                {
                    "progress": event.job.percent,
                    "current": event.current,
                    "total": event.total,
                    "message": event.message,
                }
            )

        elif isinstance(event, JobCompletedEvent):
            # Safe unpack in case result is wrapped in a JobResult object
            result_value = getattr(event.result, "value", event.result)
            broadcast_job_event(event.job, "SUCCESS", {"result": result_value})

        elif isinstance(event, JobFailedEvent):
            broadcast_job_event(event.job, "FAILURE", {"error": str(event.exception)})