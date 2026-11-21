from typing import Type

from .subscriber import EventSubscriber
from .event import Event
from .dispatcher import EventDispatcher


def listen(event_cls: Type[Event]):
    """Decorator to register a standalone EventListener to an EventDispatcher."""
    def decorator(listener_cls):
        EventDispatcher.register(event_cls, listener_cls)
        return listener_cls
    return decorator


def subscribe(subscriber_cls: Type[EventSubscriber]):
    """Decorator to register a class containing multiple bindings."""
    instance = subscriber_cls()
    if hasattr(instance, 'subscribe'):
        instance.subscribe()
    return subscriber_cls