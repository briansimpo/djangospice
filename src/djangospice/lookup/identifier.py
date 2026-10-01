from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LookupIdentifier:
    """
    Canonical identity of a registered lookup.
    """

    app_name: str
    model_name: str

    def __post_init__(self) -> None:
        app_name = self.app_name.strip().casefold()
        model_name = self.model_name.strip().casefold()

        if not app_name:
            raise ValueError("Lookup app_name cannot be empty.")

        if not model_name:
            raise ValueError("Lookup model_name cannot be empty.")

        object.__setattr__(self, "app_name", app_name)
        object.__setattr__(self, "model_name", model_name)

    @property
    def key(self):
        return f"{self.app_name}.{self.model_name}"

    def __str__(self) -> str:
        return self.key

    @classmethod
    def from_model(cls, model) -> "LookupIdentifier":
        return cls(
            app_name=model._meta.app_label,
            model_name=model._meta.model_name,
        )