import logging
from typing import List, Type

from .celery import CeleryAdapter
from .registry import EventRegistry
from .base import BaseEvent
from .listener import EventListener

logger = logging.getLogger(__name__)


class Event:
    """Main interface for registering and dispatching events."""
    

    @classmethod
    def register(cls, event_cls: Type[BaseEvent], listener_cls: Type[EventListener]) -> None:
        """Maps an Event class to a Listener class."""
        EventRegistry.register(event_cls, listener_cls)

    @classmethod
    def listeners(cls, event_cls: Type[BaseEvent]) -> List[Type[EventListener]]:
        """Retrieves all registered listeners for a given event class."""
        return EventRegistry.get_listeners(event_cls)
    
    @classmethod
    def dispatch(cls, event: BaseEvent) -> None:
        """Dispatches the event to all registered listeners."""
        listeners = cls.listeners(type(event))
        
        if not listeners:
            logger.debug(f"Event {type(event).__name__} dispatched, but has no listeners.")
            return

        for listener_cls in listeners:
            cls._execute_listener(event, listener_cls)
            
    @classmethod
    def _execute_listener(cls, event: BaseEvent, listener_cls: Type[EventListener]) -> None:
        """Routes execution based on the listener's configuration."""
        if getattr(listener_cls, 'should_queue', False):
            celery = CeleryAdapter()
            celery.dispatch(event, listener_cls)
        else:
            cls._dispatch_sync(event, listener_cls)
                
    @classmethod
    def _dispatch_sync(cls, event: BaseEvent, listener_cls: Type[EventListener]) -> None:
        """Executes the listener synchronously in the current thread."""
        try:
            listener_instance = listener_cls()
            listener_instance.handle(event)
        except Exception as e:
            logger.exception(f"Error executing {listener_cls.__name__} for {type(event).__name__}: {str(e)}")