
import logging
import time
from typing import Any

from celery import shared_task

from .execution import ExecutionContext

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def execute_listener(self, listener_path: str, event_path: str, payload: dict[str, Any]) -> None:

    task_id = self.request.id
    start_time = time.perf_counter()

    # Reconstruct event and listener
    try:
        context = ExecutionContext.reconstruct(
            listener_path=listener_path,
            event_path=event_path,
            payload=payload,
        )

    except Exception:
        logger.exception(
            "[%s] Failed to reconstruct event execution context.",
            task_id,
        )
        raise

    listener = context.listener
    listener_cls = type(listener)

    # Execute listener
    try:
        context.execute()
    except Exception as exc:
        duration = time.perf_counter() - start_time

        logger.warning(
            "[%s] Listener %s failed after %.4fs: %s",
            task_id,
            listener_cls.__name__,
            duration,
            exc,
        )

        retry_exceptions = getattr(listener_cls, "retry_on", ())

        if retry_exceptions and isinstance(exc, retry_exceptions):

            max_retries = getattr(listener_cls, "max_retries", 3)
            countdown = getattr(listener_cls, "retry_backoff", 60)

            raise self.retry(
                exc=exc,
                max_retries=max_retries,
                countdown=countdown,
            )

        logger.exception(
            "[%s] Fatal execution failure in %s.",
            task_id,
            listener_cls.__name__,
        )
        raise
