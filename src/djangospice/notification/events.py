from dataclasses import dataclass
from typing import Any

from djangospice.events import BaseEvent
from .payload import Payload


@dataclass
class NotificationEvent(BaseEvent):
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
class NotificationReadAll(BaseEvent):
    name = "notification_read_all"
    recipient: Any
