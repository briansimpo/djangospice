from __future__ import annotations

from dataclasses import dataclass, field
from djangospice.core.serializable import Serializable
from djangospice.core.payload import Payload


@dataclass(slots=True, kw_only=True)
class HTMXLocation(Serializable):
    """
    Represents the value of the HX-Location response header.
    """

    path: str

    target: str | None = None
    swap: str | None = None
    select: str | None = None

    values: Payload = field(default_factory=Payload)
    headers: Payload = field(default_factory=Payload)
    