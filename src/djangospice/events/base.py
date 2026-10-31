
from abc import ABC
from dataclasses import dataclass, field
from slugify import slugify

from djangospice.core.serializable import Serializable


@dataclass(kw_only=True)
class BaseEvent(Serializable, ABC):
    """
    Base class for all events.

    Subclasses can define a class-level name or have one
    automatically generated from their class name.
    """

    name: str = field(default="base_event")

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Capture explicitly declared name or generate one.
        if "name" in cls.__dict__:
            event_name = cls.__dict__["name"]
        else:
            event_name = slugify(cls.__name__, separator="_")

        cls.name = event_name

    def __post_init__(self):
        self.name = type(self).name

    def __str__(self) -> str:
        return self.name
