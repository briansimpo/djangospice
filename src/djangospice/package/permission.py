from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Permission:
    codename: str
    name: str
    description: str = ""

    def __post_init__(self) -> None:
        if not self.codename.strip():
            raise ValueError("Permission codename cannot be empty.")
        if not self.name.strip():
            raise ValueError("Permission name cannot be empty.")

    def qualified(self, app_key: str) -> str:
        """Return the Djangospice-qualified permission identifier."""
        return f"{app_key}.{self.codename}"
