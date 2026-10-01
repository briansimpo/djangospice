from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from djangospice.core.serializable import Serializable


@dataclass(slots=True, kw_only=True)
class HTMXLocation(Serializable):
    """
    Represents the value of the HX-Location response header.
    """

    path: str

    target: str | None = None
    swap: str | None = None
    select: str | None = None

    values: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, Any] = field(default_factory=dict)
    