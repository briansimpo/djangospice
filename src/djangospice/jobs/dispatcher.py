from __future__ import annotations

import uuid
from django.db import transaction

from djangospice.events import Event
from .base import Job
from .celery import CeleryAdapter
from .enums import JobStatus
from .handle import JobHandle
from .events import JobQueuedEvent


class JobDispatcher:
    """
    Domain orchestrator responsible for queue selection, ID assignment, 
    and transaction isolation boundaries.
    """

    @classmethod
    def dispatch(cls, job: Job, queue: str | None = None, seconds: int | float = 0, minutes: int | float = 0, hours: int | float = 0) -> JobHandle:
        target_queue = queue or job.queue
        
        # 1. Generate unique identifier instantly on trigger side
        job_id = str(uuid.uuid4())
        job._id = job_id
        job.status = JobStatus.QUEUED

        # 2. Compute the exact scheduled delay
        total_seconds = seconds + (minutes * 60) + (hours * 3600)
        countdown = total_seconds if total_seconds > 0 else None

        # 3. Freeze recursive object snapshot
        serialized_payload = job.to_dict()

        def _enqueue():
            # Broadcast queued state to your WebSocket listeners safely on commit
            Event.dispatch(JobQueuedEvent(job=job))
            
            # Pass full execution context to the adapter
            celery = CeleryAdapter()
            celery.dispatch(
                serialized_job=serialized_payload,
                queue=target_queue,
                countdown=countdown,
                task_id=job_id,
                timeout=job.timeout,
            )
            
        # Protect broker integrity by waiting for database commits
        transaction.on_commit(_enqueue)

        return JobHandle(job_id=job_id)