from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from djangospice.core.serializable import Serializable


@dataclass(frozen=True, slots=True)
class Link(Serializable):
    """
    Describes where a notification should take the user.
    """

    url: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Action(Serializable):
    """
    Represents an action available to the user from a notification.
    """

    label: str
    link: Link
    icon: str | None = None
    style: Literal[
        "primary",
        "secondary",
        "success",
        "warning",
        "danger",
    ] = "primary"


@dataclass(slots=True, kw_only=True)
class Metadata(Serializable):
    """
    Structured data associated with a notification.

    Persisted in Notification.data.
    """

    type: str
    category: str

    link: Link | None = None
    actions: list[Action] = field(default_factory=list)

    icon: str | None = None
    image: str | None = None

    context: dict[str, Any] = field(default_factory=dict)
    messages: dict[str, Any] = field(default_factory=dict)
    