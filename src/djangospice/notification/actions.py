from dataclasses import dataclass, field
from typing import Literal

from djangospice.core.serializable import Serializable


@dataclass(frozen=True, slots=True)
class Action(Serializable):
    name: str
    url: str
    label: str | None = None
    icon: str | None = None
    method: Literal["get", "post"] = "get"
    style: Literal["primary", "secondary", "success", "warning", "danger"] = "primary"

    def __post_init__(self):
        if self.label is None:
            label = self.name.replace("_", " ").replace("-", " ").title()
            object.__setattr__(self, "label", label)


@dataclass(frozen=True, slots=True)
class PostAction(Action):
    method: Literal["post"] = field(default="post", init=False)


@dataclass(frozen=True, slots=True)
class GetAction(Action):
    method: Literal["get"] = field(default="get", init=False)