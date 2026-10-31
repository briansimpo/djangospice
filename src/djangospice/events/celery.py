
from functools import partial
import logging

from django.db import transaction

from .base import BaseEvent
from .listener import EventListener
from .tasks import execute_listener


logger = logging.getLogger(__name__)


class CeleryAdapter:

    def dispatch(self, event: BaseEvent, listener_cls: type[EventListener]) -> None:

        listener_path = f"{listener_cls.__module__}.{listener_cls.__qualname__}"

        event_path = f"{type(event).__module__}.{type(event).__qualname__}"

        payload = event.to_dict()

        transaction.on_commit(
            partial(
                execute_listener.delay,
                listener_path,
                event_path,
                payload,
            )
        )