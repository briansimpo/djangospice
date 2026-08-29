from __future__ import annotations

from dataclasses import dataclass

from djangospice.html.attributes import HTMXAttributes


@dataclass(frozen=True, slots=True)
class Interaction:
    url: str
    htmx: HTMXAttributes