from abc import ABC
from typing import ClassVar
from slugify import slugify
from dataclasses import dataclass

from djangospice.core.serializable import Serializable


@dataclass(kw_only=True)
class BaseEvent(Serializable, ABC):
    """
    Base class for all events. 
    Auto-generates 'name' in snake_case if not provided in the subclass.
    """
    
    name: ClassVar[str] = "base_event"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        if 'name' not in cls.__dict__:
            cls.name = slugify(cls.__name__, separator="_")

    def __str__(self) -> str:
        return self.name
    
    