from __future__ import annotations

from threading import RLock

from .definition import LookupDefinition
from .exceptions import LookupConfigurationError


class LookupRegistry:
    """
    Registry of explicitly exposed model lookups.
    """

    def __init__(self) -> None:
        self._definitions: dict[str,LookupDefinition] = {}
        self._lock = RLock()

    def register(self, definition: LookupDefinition) -> LookupDefinition:
        identifier = definition.identifier

        with self._lock:
            if identifier in self._definitions:
                existing = self._definitions[identifier]

                raise LookupConfigurationError(
                    f"Lookup '{definition.identifier}' is already "
                    f"registered for "
                    f"{existing.model._meta.label}."
                )

            self._definitions[identifier] = definition

        return definition

    def get(self, identifier: str) -> LookupDefinition:
    
        with self._lock:
            try:
                return self._definitions[identifier]
            except KeyError as exc:
                raise LookupConfigurationError(
                    f"Unknown lookup: {identifier}."
                ) from exc

    def has(self, identifier: str) -> bool:
        with self._lock:
            return identifier in self._definitions

    def unregister(self, identifier: str) -> None:

        with self._lock:
            self._definitions.pop(
                identifier,
                None,
            )

    def all(self) -> tuple[LookupDefinition, ...]:
        with self._lock:
            return tuple(self._definitions.values())

    def clear(self) -> None:
        with self._lock:
            self._definitions.clear()


lookup_registry = LookupRegistry()