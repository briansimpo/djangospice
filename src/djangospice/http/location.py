from __future__ import annotations

import json

from dataclasses import dataclass

from djangospice.core.serializable import Serializable


@dataclass(slots=True, kw_only=True)
class HTMXLocation(Serializable):

    path: str
    target: str | None = None
    swap: str | None = None
    select: str | None = None

    def to_dict(self) -> dict[str, str]:
        location = {"path": self.path}

        if self.target:
            location["target"] = self.target

        if self.swap:
            location["swap"] = self.swap

        if self.select:
            location["select"] = self.select

        return location

    def to_json(self) -> str:
        return json.dumps(self.to_dict())