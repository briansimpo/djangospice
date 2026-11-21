
from __future__ import annotations

from typing import Any
from celery import Task

from djangospice.websocket.broadcast import Broadcast

from .job import Job
from .enums import JobStatus


class JobReporter:
    """
    Coordinates job lifecycle state and realtime broadcasting.
    """

    def __init__(self, task: Task = None) -> None:
        self.task = task

    def _publish(self, job: Job, event: str, **extra: Any ) -> None:
        data = {
            **job.to_status(),
            **extra,
        }

        if self.task:
            self.task.update_state(
                state=job.status.upper(),
                meta=data,
            )

        Broadcast.event(
            event=event,
            user=job.user_id,
            data=data
        )

    def queued(self, job: Job) -> None:
        job.status = JobStatus.QUEUED

        self._publish(job, "job_queued")

    def started(self, job: Job) -> None:
        job.status = JobStatus.STARTED

        self._publish(job, "job_started")

    def progress(self, job: Job, current: int, total: int, message: str = "", **extra: Any) -> None:
        job.current = current
        job.total = total
        job.status = JobStatus.RUNNING

        self._publish(
            job,
            "job_progressed",
            message=message,
            extra=extra,
        )

    def retrying(self, job: Job, exception: Exception, countdown: int = 0) -> None:
        job.status = JobStatus.RETRYING

        self._publish(
            job,
            "job_retrying",
            error=str(exception),
            countdown=countdown,
        )

    def completed(self, job: Job, job_result=None) -> None:
        job.current = job.total
        job.status = JobStatus.SUCCESS

        result = job_result.result if job_result else None

        self._publish(
            job,
            "job_completed",
            result=result,
        )

    def failed(self, job: Job, exception: Exception) -> None:
        job.status = JobStatus.FAILURE

        self._publish(
            job,
            "job_failed",
            error=str(exception),
        )
