from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class LookupQuery:
    """
    A framework-independent lookup request.

    The HTTP layer translates request parameters into this object.
    """

    model: Any

    search: str = ""

    filters: Mapping[str, Any] = field(
        default_factory=dict,
    )

    page: int = 1

    page_size: int = 20

    @property
    def normalized_page(self) -> int:
        return max(self.page, 1)

    @property
    def normalized_page_size(self) -> int:
        return min(
            max(self.page_size, 1),
            100,
        )