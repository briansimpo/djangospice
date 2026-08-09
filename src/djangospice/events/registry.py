from collections import defaultdict
from typing import Dict, List, Type

from .base import BaseEvent
from .listener import EventListener


class EventRegistry:
    """Handles the storage and retrieval of Event to Listener mappings."""
    _registry: Dict[Type[BaseEvent], List[Type[EventListener]]] = defaultdict(list)

    @classmethod
    def register(cls, event_cls: Type[BaseEvent], listener_cls: Type[EventListener]) -> None:
        if not issubclass(event_cls, BaseEvent):
            raise ValueError(f"{event_cls.__name__} must inherit from BaseEvent.")
        if not issubclass(listener_cls, EventListener):
            raise ValueError(f"{listener_cls.__name__} must inherit from EventListener.")
        
        if listener_cls not in cls._registry[event_cls]:
            cls._registry[event_cls].append(listener_cls)

    @classmethod
    def get_listeners(cls, event_cls: Type[BaseEvent]) -> List[Type[EventListener]]:
        listeners = cls._registry.get(event_cls, [])
        return sorted(listeners, key=lambda x: getattr(x, "priority", 100))

