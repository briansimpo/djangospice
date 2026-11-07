from dataclasses import dataclass

from djangospice.notification.actions import Action
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
    actions: tuple[Action, ...] = ()

    def get_actions(self):
        return [action.to_dict() for action in self.actions]
