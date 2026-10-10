from __future__ import annotations

from dataclasses import dataclass, field

from djangospice.core.serializable import Serializable
from djangospice.routing import safe_reverse

from .apps import namespace
from .models import Notification


@dataclass(frozen=True, slots=True)
class NotificationURLs(Serializable):
    """
    Client URLs for notification actions.
    """

    read: str | None = None
    unread: str | None = None
    delete: str | None = None


@dataclass(frozen=True, slots=True)
class NotificationPayload(Serializable):
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

    actor_object_id: str | None = None
    target_object_id: str | None = None

    slug: str | None = None
    text: str | None = None

    unread: bool | None = None
    public: bool | None = None

    urls: NotificationURLs = field(
        default_factory=NotificationURLs,
    )

    @classmethod
    def from_model(
        cls,
        notification: Notification,
    ) -> "NotificationPayload":
        slug = notification.slug

        return cls(
            id=str(notification.pk),
            recipient_id=str(notification.recipient_id),

            actor_object_id=(
                str(notification.actor_object_id)
                if notification.actor_object_id is not None
                else None
            ),

            target_object_id=(
                str(notification.target_object_id)
                if notification.target_object_id is not None
                else None
            ),

            verb=notification.verb,
            description=notification.description,
            level=notification.level,

            unread=notification.unread,
            public=notification.public,

            slug=slug,
            text=str(notification),

            urls=NotificationURLs(
                read=safe_reverse(
                    "api-mark-read",
                    namespace,
                    kwargs={"slug": slug},
                ),
                unread=safe_reverse(
                    "api-mark-unread",
                    namespace,
                    kwargs={"slug": slug},
                ),
                delete=safe_reverse(
                    "api-delete",
                    namespace,
                    kwargs={"slug": slug},
                ),
            ),
        )