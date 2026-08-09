from __future__ import annotations

import contextvars
from typing import Any
from djangospice.events.dispatcher import Event

from .base import Job
from .enums import JobStatus
from .events import (
    JobQueuedEvent,
    JobStartedEvent,
    JobProgressedEvent,
    JobCompletedEvent,
    JobFailedEvent,
)

active_reporter: contextvars.ContextVar[JobReporter | None] = contextvars.ContextVar(
    "active_reporter", default=None
)


class JobReporter:
    """Orchestrates job status updates and dispatches native domain events."""

    def __init__(self, task: Any = None) -> None:
        self.task = task

    def _sync_celery_meta(self, state: JobStatus, meta: dict[str, Any]) -> None:
        """Syncs progress or failure metadata back to the Celery broker."""
        if self.task:
            self.task.update_state(state=state, meta=meta)

    def queued(self, job: Job) -> None:
        job.status = JobStatus.QUEUED
        self._sync_celery_meta(job.status, {"status": "QUEUED"})
        Event.dispatch(JobQueuedEvent(job=job))

    def started(self, job: Job) -> None:
        job.status = JobStatus.STARTED
        self._sync_celery_meta(job.status, {"percent": 0})
        Event.dispatch(JobStartedEvent(job=job))

    def progress(self, job: Job, *, current: int, total: int, message: str = "", **extra) -> None:
        job.current = current
        job.total = total
        job.status = JobStatus.PROGRESS
        
        self._sync_celery_meta(job.status, {
            "current": current,
            "total": total,
            "percent": job.percent,
            "message": message,
            **extra
        })
        Event.dispatch(JobProgressedEvent(
            job=job, 
            current=current, 
            total=total, 
            message=message, 
            extra=extra
        ))

    def completed(self, job: Job, *, result: Any = None) -> None:
        job.current = getattr(job, "total", 100)
        job.status = JobStatus.COMPLETED
        
        # Unpack value safely if wrapped in a JobResult container
        result_value = getattr(result, "value", result)
        
        self._sync_celery_meta(job.status, {
            "percent": 100,
            "result": result_value
        })
        Event.dispatch(JobCompletedEvent(job=job, result=result))

    def failed(self, job: Job, exception: Exception) -> None:
        job.status = JobStatus.FAILURE
        self._sync_celery_meta(job.status, {"exception": str(exception)})
        Event.dispatch(JobFailedEvent(job=job, exception=exception))