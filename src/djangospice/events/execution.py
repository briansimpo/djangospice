
from dataclasses import dataclass
from typing import Any, Type

from djangospice.core.resolver import resolve_class 

from .base import BaseEvent
from .listener import EventListener


@dataclass
class ExecutionContext:
    event: BaseEvent
    listener: EventListener

    @classmethod
    def reconstruct(cls, listener_path: str, event_path: str, payload: dict[str, Any]) -> "ExecutionContext":

        event_cls: Type[BaseEvent] = resolve_class(event_path)
        listener_cls: Type[EventListener] = resolve_class(listener_path)

        event = event_cls.from_dict(payload)
        listener = listener_cls()

        return cls(
            event=event,
            listener=listener,
        )

    def execute(self) -> None:
        self.listener.handle(self.event)
