import logging
import time
from typing import Any, Type

from celery import shared_task

from djangospice.core.serializer import resolve_class  
from .base import BaseEvent
from .listener import EventListener

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def execute_listener(self, listener_path: str, event_path: str, payload: dict[str, Any]) -> None:
   
    task_id = self.request.id
    logger.info(f"[{task_id}] Initiating execution: {listener_path} for event {event_path}")
    
    start_time = time.perf_counter()

    # 1. Attempt Deserialization
    try:
        event_cls: Type[BaseEvent] = resolve_class(event_path)
        listener_cls: Type[EventListener] = resolve_class(listener_path)
        
        # Hydrate the dictionary payload back into a rich typed dataclass instance
        event = event_cls.from_dict(payload)
        
    except Exception as exc:
        logger.error(
            f"[{task_id}] Deserialization crash! Class path resolution or "
            f"database model pre-fetching failed. Payload: {payload}",
            exc_info=True
        )
        # Raising immediately since data-corruption/schema-drift issues aren't retriable
        raise exc

    # 2. Execute Business Logic with performance telemetry
    try:
        listener_instance = listener_cls()
        listener_instance.handle(event)
        
        duration = time.perf_counter() - start_time
        logger.info(f"[{task_id}] Successfully executed {listener_cls.__name__} in {duration:.4f}s.")

    except Exception as exc:
        duration = time.perf_counter() - start_time
        logger.warning(
            f"[{task_id}] Handled execution failure in {listener_cls.__name__} "
            f"after {duration:.4f}s: {exc}"
        )

        # 3. Smart Transient Retry Handling
        # Check if the listener defines specific exceptions it wants to retry on
        retry_exceptions = getattr(listener_cls, "retry_on", ())
        
        if retry_exceptions and isinstance(exc, retry_exceptions):
            max_retries = getattr(listener_cls, "max_retries", 3)
            countdown = getattr(listener_cls, "retry_backoff", 60)
            
            logger.warning(
                f"[{task_id}] Transient exception matching policy detected! "
                f"Scheduling retry ({self.request.retries + 1}/{max_retries}) "
                f"in {countdown}s..."
            )
            
            raise self.retry(
                exc=exc, 
                max_retries=max_retries, 
                countdown=countdown
            )
            
        # Hard fail if the exception is not on the retry list or retries are exhausted
        logger.exception(f"[{task_id}] Fatal execution failure in {listener_cls.__name__}.")
        raise exc