from dataclasses import dataclass

from djangospice.events import BaseEvent

from .payload import NotificationPayload


@dataclass
class NotificationEvent(BaseEvent):
    payload: NotificationPayload


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