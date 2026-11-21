
from dataclasses import dataclass
from typing import Any, Type

from djangospice.core.resolver import resolve_class 

from .event import Event
from .listener import EventListener


@dataclass
class Execution:
    event: Event
    listener: EventListener

    @classmethod
    def construct(cls, listener_path: str, event_path: str, payload: dict[str, Any]) -> "Execution":

        event_cls: Type[Event] = resolve_class(event_path)
        listener_cls: Type[EventListener] = resolve_class(listener_path)

        event = event_cls.from_dict(payload)
        listener = listener_cls()

        return cls(
            event=event,
            listener=listener,
        )

    def execute(self) -> None:
        self.listener.handle(self.event)
