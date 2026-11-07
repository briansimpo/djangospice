from dataclasses import dataclass, field

from djangospice.core.executable import Action
from .base import Message


@dataclass(kw_only=True)
class DatabaseMessage(Message):
    """
    Message stored directly in the database.
    Used primarily for persistent, in-app notification centers.
    """

    title: str
    body: str
    icon: str | None = None
    image: str | None = None
    url: str | None = None
    actions: list[Action] = field(default_factory=list)

    def get_actions(self):
        return self.actions
