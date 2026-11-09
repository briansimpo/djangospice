from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Lookup:

    field_name: str
    options: dict[str, Any] = field(default_factory=dict)

    def __init__(self, field_name: str | None = None,  **options):
        if not field_name:
            raise ValueError(
                "Lookup requires a field_name."
            )

        self.field_name = field_name
        self.options = options

