from __future__ import annotations

import uuid

from .celery import CeleryAdapter
from .enums import JobStatus
from .handle import JobHandle
from .job import Job


class JobDispatcher:
    """
    Domain orchestrator responsible for queue selection, ID assignment, 
    and transaction isolation boundaries.
    """

    @classmethod
    def dispatch(cls, job: Job) -> JobHandle:

        job_id = str(uuid.uuid4())
        job._id = job_id
        job.status = JobStatus.QUEUED
       
        celery = CeleryAdapter()
        celery.dispatch(job)
        
        return JobHandle(job_id=job_id)

