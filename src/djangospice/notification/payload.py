from __future__ import annotations

from dataclasses import dataclass

from djangospice.core.serializable import Serializable
from .models import Notification


@dataclass
class Payload(Serializable):
    """
    Serializable representation of a persisted notification.

    Used by notification events, realtime transports, and
    client-facing HTTP responses.
    """

    id: str
    recipient_id: str
    verb: str
    description: str
    level: str
    slug: str | None = None
    text: str | None = None
    unread: bool | None = None
    public: bool | None = None
    timespan: str | None = None


    @classmethod
    def from_model(cls, notification: Notification) -> "Payload":
        slug = str(notification.slug)

        return cls(
            id=str(notification.pk),
            recipient_id=str(notification.recipient_id),
            verb=notification.verb,
            description=notification.description,
            level=notification.level,
            unread=notification.unread,
            public=notification.public,
            text=str(notification),
            slug=slug,
            timespan=notification.timespan,
        )
            

def payload(notification: Notification):
    return Payload.from_model(notification)
