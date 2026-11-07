from __future__ import annotations

from typing import Any, Literal
from copy import deepcopy
from dataclasses import dataclass, field
from djangospice.core.serializable import Serializable

from .conf import ActionStyle, ACTION_STYLES


@dataclass(frozen=True, slots=True)
class Action(Serializable):
    """Serializable representation of an executable action."""

    name: str
    url: str
    label: str | None = None
    icon: str | None = None
    method: Literal["get", "post"] = "get"
    style: ActionStyle = "primary"
    status: str = "pending"
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        method = self.method.lower()

        if method not in {"get", "post"}:
            raise ValueError(
                f"Unsupported action method: {method}"
            )

        if self.style not in ACTION_STYLES:
            raise ValueError(
                f"Invalid action style: {self.style}"
            )

        object.__setattr__(self, "method", method)
        object.__setattr__(
            self,
            "attributes",
            deepcopy(self.attributes),
        )

        if self.label is None:
            label = (
                self.name
                .replace("_", " ")
                .replace("-", " ")
                .title()
            )
            object.__setattr__(self, "label", label)


@dataclass(frozen=True, slots=True)
class PostAction(Action):
    method: Literal["post"] = field(
        default="post",
        init=False,
    )


@dataclass(frozen=True, slots=True)
class GetAction(Action):
    method: Literal["get"] = field(
        default="get",
        init=False,
    )

