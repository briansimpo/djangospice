from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode


@dataclass(frozen=True, slots=True)
class QueryState:
    values: tuple[tuple[str, tuple[str, ...]], ...] = ()

    @classmethod
    def from_querydict(cls, querydict: Any) -> "QueryState":
        return cls(
            tuple(
                (key, tuple(values))
                for key, values in querydict.lists()
            )
        )

    def has(self, name: str) -> bool:
        """Check if a query parameter exists in the state."""
        return any(key == name for key, _ in self.values)

    def get(self, name: str) -> str | None:
        """Get the last string value for a given parameter name."""
        data = dict(self.values)
        values = data.get(name)
        return values[-1] if values else None

    def getlist(self, name: str) -> tuple[str, ...]:
        """Get all string values for a given parameter name."""
        data = dict(self.values)
        return data.get(name, ())

    def set(self, name: str, value: object | None) -> "QueryState":
        data = dict(self.values)

        if value is None or value == "":
            data.pop(name, None)
        else:
            data[name] = (str(value),)

        return QueryState(tuple(data.items()))

    def remove(self, *names: str) -> "QueryState":
        return QueryState(
            tuple(
                (key, values)
                for key, values in self.values
                if key not in names
            )
        )

    def encode(self) -> str:
        return urlencode(
            [
                (key, value)
                for key, values in self.values
                for value in values
            ]
        )