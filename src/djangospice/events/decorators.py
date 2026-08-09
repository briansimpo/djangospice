from typing import Type

from .subscriber import EventSubscriber
from .base import BaseEvent
from .dispatcher import Event


def listen(event_cls: Type[BaseEvent]):
    """Decorator to register a standalone EventListener to an Event."""
    def decorator(listener_cls):
        Event.register(event_cls, listener_cls)
        return listener_cls
    return decorator


def subscribe(subscriber_cls: Type[EventSubscriber]):
    """Decorator to register a class containing multiple bindings."""
    instance = subscriber_cls()
    if hasattr(instance, 'subscribe'):
        instance.subscribe()
    return subscriber_cls