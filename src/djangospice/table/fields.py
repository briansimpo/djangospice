from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Field:
    name: str
    label: str | None = None
    accessor: str | None = None
    sortable: bool = True
    searchable: bool = False
    visible: bool = True
    exclude: bool = False
    empty_value: Any = None
    attrs: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.label is None:
            object.__setattr__(
                self,
                "label",
                self.name.replace("__", " ").replace("_", " ").title(),
            )

        if self.accessor is None:
            object.__setattr__(self, "accessor", self.name)

    @classmethod
    def normalize(cls, value: Field | str) -> Field:
        if isinstance(value, cls):
            return value

        if isinstance(value, str):
            return cls(name=value)

        raise TypeError(
            f"Expected Field or str, got {type(value).__name__}."
        )