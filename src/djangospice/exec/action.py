from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Literal
from functools import cached_property

from djangospice.core.collection import ObjectCollection
from djangospice.core.serializable import Serializable

from .conf import ActionStyle, ACTION_STYLES


@dataclass(frozen=True, slots=True)
class Action(Serializable):
    """Serializable representation of an executable action."""

    name: str
    url: str

    # Presentation
    label: str | None = None
    icon: str | None = None
    style: ActionStyle = "primary"

    # Classification
    group: str | None = None

    # Behavior
    method: Literal["get", "post"] = "get"
    confirm: str | None = None
    is_link: bool = False
    open_tab: bool = False

    # Ordering and visibility
    order: int = 1
    visible: bool = True
    perms: tuple[str, ...] = ()

    # Semantic styling
    is_danger: bool = False
    is_primary: bool = False

    # Runtime state
    status: str = "pending"

    # Additional attributes
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
        object.__setattr__(self, "perms", tuple(self.perms))
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


class Actions(ObjectCollection[Action]):
    """
    Immutable collection of widget actions.

    Provides fast lookup by name and efficient grouping for rendering.
    """

    @cached_property
    def _map(self) -> dict[str, Action]:
        return {
            action.name: action
            for action in self._items
        }

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------

    def get(self, name: str) -> Action | None:
        return self._map.get(name)

    def require(self, name: str) -> Action:
        try:
            return self._map[name]
        except KeyError:
            raise KeyError(
                f"Unknown action '{name}'"
            ) from None
