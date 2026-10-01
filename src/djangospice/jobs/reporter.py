from __future__ import annotations

import contextvars
from typing import Any

from djangospice.events.dispatcher import Event

from .base import Job
from .enums import JobStatus
from .result import JobResult

from .events import (
    JobQueued,
    JobStarted,
    JobProgressed,
    JobCompleted,
    JobFailed,
)


active_reporter: contextvars.ContextVar[JobReporter | None] = contextvars.ContextVar(
    "active_reporter",
    default=None,
)


class JobReporter:
    """Orchestrates job status updates and dispatches native domain events."""

    def __init__(self, task: Any = None) -> None:
        self.task = task

    def _sync_celery_meta(self, state: JobStatus, meta: dict[str, Any]) -> None:
        """Sync job state and metadata back to the Celery task."""
        if self.task:
            self.task.update_state(
                state=state,
                meta=meta,
            )

    def queued(self, job: Job) -> None:
        job.status = JobStatus.QUEUED

        self._sync_celery_meta(job.status,
            {
                "status": job.status.value,
            },
        )

        Event.dispatch(
            JobQueued(
                job=job,
            )
        )

    def started(self, job: Job) -> None:
        job.status = JobStatus.STARTED

        self._sync_celery_meta(
            job.status,
            {
                "percent": 0,
            },
        )

        Event.dispatch(
            JobStarted(
                job=job,
            )
        )

    def progress(self,job: Job, current: int, total: int, message: str = "", **extra: Any) -> None:
        job.current = current
        job.total = total
        job.status = JobStatus.PROGRESS

        self._sync_celery_meta(
            job.status,
            {
                "current": current,
                "total": total,
                "percent": job.percent,
                "message": message,
                **extra,
            },
        )

        Event.dispatch(
            JobProgressed(
                job=job,
                message=message,
                extra=extra,
            )
        )

    def completed(self,job: Job, job_result: JobResult = None) -> None:
        job.current = job.total
        job.status = JobStatus.COMPLETED

        result = job_result.result if job_result else None

        self._sync_celery_meta(
            job.status,
            {
                "percent": job.percent,
                "result": result,
            },
        )

        Event.dispatch(
            JobCompleted(
                job=job,
                result=result,
            )
        )

    def failed(self, job: Job, exception: Exception) -> None:
        job.status = JobStatus.FAILURE

        error = str(exception)

        self._sync_celery_meta(
            job.status,
            {
                "error": error,
            },
        )

        Event.dispatch(
            JobFailed(
                job=job,
                error=error,
            )
        )