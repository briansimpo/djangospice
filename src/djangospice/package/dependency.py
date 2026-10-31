from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Dependency:
    key: str
    version_specifier: str = ""
    optional: bool = False

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("Dependency key cannot be empty.")
