from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal

from djangospice.core.serializable import Serializable
from djangospice.core.payload import Payload


@dataclass(frozen=True, slots=True)
class NotificationIntent(Serializable):
    """
    Describes the semantic destination or action associated with a
    notification.

    The frontend resolves the intent into the appropriate navigation
    mechanism for the current platform (HTMX, SPA, mobile, desktop).
    """

    name: str
    parameters: Payload = field(default_factory=Payload)
    metadata: Payload = field(default_factory=Payload)
    
    
    
@dataclass(frozen=True, slots=True)
class NotificationAction(Serializable):
    """
    Represents an action the user may perform from a notification.
    """

    label: str
    intent: NotificationIntent
    icon: str | None = None
    style: Literal[
        "primary",
        "secondary",
        "success",
        "warning",
        "danger",
    ] = "primary"
    
    

@dataclass(slots=True, kw_only=True)
class NotificationData(Serializable):
    """
    Structured data persisted in Notification.data.

    This wraps all framework metadata, UI metadata, business payload,
    and channel-specific message payloads.
    """

    # Framework metadata
    type: str
    category: str

    # UI metadata
    intent: NotificationIntent | None = None
    actions: list[NotificationAction] = field(default_factory=list)
    icon: str | None = None
    image: str | None = None

    # Business payload
    payload: Payload = field(default_factory=Payload)

    # Serialized channel messages
    messages: dict[str, dict[str, Any]] = field(default_factory=dict)