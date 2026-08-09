from abc import ABC, abstractmethod
from typing import Type
from .base import BaseEvent


class EventListener(ABC):
    """
    Base class for handling a specific event.
    """
    should_queue: bool = True
    queue_name: str = 'default'  
    priority: int = 100

    retry_on: tuple[Type[Exception], ...] = ()
    max_retries: int = 3
    retry_backoff: int = 60 

    @abstractmethod
    def handle(self, event: BaseEvent) -> None:
        """Executes the business logic reacting to the event."""
        pass