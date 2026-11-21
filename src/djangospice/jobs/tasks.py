
import logging
from typing import Any

from celery import shared_task

from .execution import Execution

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def execute_job(self, job_path: str, payload: dict[str, Any]) -> None:

    task_id = self.request.id

    try:
        execution = Execution.construct(
            job_path=job_path,
            payload=payload,
        )

    except Exception:
        logger.exception(
            "[%s] Failed to reconstruct job execution context.",
            task_id,
        )
        raise

    execution.execute(task=self)
