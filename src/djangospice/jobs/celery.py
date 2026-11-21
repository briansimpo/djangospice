from __future__ import annotations

from functools import partial
from django.db import transaction

from .job import Job
from .tasks import execute_job


class CeleryAdapter:
    """
    Dispatches serialized job payloads immediately to the Celery broker
    """

    def dispatch(self, job: Job) -> None:
    
        job_path = f"{type(job).__module__}.{type(job).__qualname__}"

        payload = job.to_dict()

        transaction.on_commit(
            partial(
                execute_job.delay,
                job_path,
                payload,
            )
        )