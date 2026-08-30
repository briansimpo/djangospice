from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LookupOption:
    value: str
    label: str
    description: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "label": self.label,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class LookupResult:
    options: tuple[LookupOption, ...]

    page: int
    page_size: int
    total: int

    has_next: bool
    has_previous: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "results": [
                option.as_dict()
                for option in self.options
            ],
            "pagination": {
                "page": self.page,
                "page_size": self.page_size,
                "total": self.total,
                "has_next": self.has_next,
                "has_previous": self.has_previous,
            },
        }