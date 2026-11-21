from dataclasses import dataclass
from typing import Any

from djangospice.events import Event
from .payload import Payload


@dataclass
class NotificationEvent(Event):
    notification: Payload


@dataclass
class NotificationCreated(NotificationEvent):
    name = "notification_created"


@dataclass
class NotificationRead(NotificationEvent):
    name = "notification_read"


@dataclass
class NotificationUnread(NotificationEvent):
    name = "notification_unread"


@dataclass
class NotificationDeleted(NotificationEvent):
    name = "notification_deleted"


@dataclass
class NotificationReadAll(Event):
    name = "notification_read_all"
    recipient: Any
