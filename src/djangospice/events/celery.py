from functools import partial
import logging
from typing import Type

from django.db import transaction

from .base import BaseEvent
from .listener import EventListener
from .tasks import execute_listener 

logger = logging.getLogger(__name__)


class CeleryAdapter:
    """Adapts async event dispatching to Celery and Django's transaction queue."""

    def dispatch(self, event: BaseEvent, listener_cls: Type[EventListener]) -> None:
        queue_name = getattr(listener_cls, "queue_name", None)

        # 1. Standardized serialization via the event's native Serializable interface
        payload = event.to_dict()

        # 2. Build task payload pointing to classpath string representations
        task_kwargs = {
            "listener_path": f"{listener_cls.__module__}.{listener_cls.__name__}",
            "event_path": f"{event.__class__.__module__}.{event.__class__.__name__}",
            "payload": payload,
        }

        # 3. Queue execution safely after the current database transaction commits
        transaction.on_commit(
            partial(
                execute_listener.apply_async,
                kwargs=task_kwargs,
                queue=queue_name,
            )
        )

        logger.debug(
            f"Queued async execution of {listener_cls.__name__} "
            f"for {type(event).__name__}."
        )