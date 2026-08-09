from __future__ import annotations

import logging
from typing import Any

from celery.exceptions import OperationalError

logger = logging.getLogger(__name__)


class CeleryAdapter:
    """
    Dispatches serialized job payloads immediately to the Celery broker
    """

    def dispatch(self,
        serialized_job: dict[str, Any],
        queue: str,
        countdown: float | None = None,
        task_id: str | None = None,
        timeout: int | float | None = None,
        priority: int | None = None,
    ) -> str:
        from .tasks import execute_job  # Deferred import to avoid circulars

        # 1. Base dispatch options
        options: dict[str, Any] = {
            "queue": queue,
        }

        # 2. Assign scheduling and identities
        if countdown is not None:
            options["countdown"] = countdown
        if task_id is not None:
            options["task_id"] = task_id
        if priority is not None:
            options["priority"] = priority

        # 3. Dynamic Timeout Mapping
        # Mapping your job's generic timeout to Celery's hard and soft worker limits
        if timeout is not None:
            options["soft_time_limit"] = int(timeout)
            options["time_limit"] = int(timeout) + 15  # 15s grace period before hard SIGKILL

        # 4. Message Broker Resilience (Producer Retries)
        # If your Redis/RabbitMQ server is temporarily restarting or experiences
        # a transient network drop, Celery will transparently attempt redelivery.
        options["retry"] = True
        options["retry_policy"] = {
            "max_retries": 3,         # Try up to 3 times
            "interval_start": 0.2,    # Wait 0.2s before first retry
            "interval_step": 0.2,     # Add 0.2s backoff delay to subsequent retries
            "interval_max": 1.0,      # Cap the wait at 1 second
        }

        try:
            celery_task = execute_job.apply_async(
                args=[serialized_job],
                **options
            )
            return celery_task.id

        except OperationalError as exc:
            # Explicit broker crash protection and critical alerts
            logger.critical(
                f"Celery broker is unreachable! Could not queue task '{task_id or 'unknown'}'. "
                f"Error details: {exc}",
                exc_info=True
            )
            raise