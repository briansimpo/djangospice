from __future__ import annotations

from typing import Any, Self

from djangospice.core.payload import Payload


class Event(Payload):
    """
    Collection of client-side events.

    Example
    -------
    >>> events = Event()
    >>> events.event("saved", id=1)
    >>> events.event("refreshTable")
    """

    def add(self, name: str, payload: dict[str, Any] | Payload | None = None) -> Self:
        """
        Add or replace an event.

        Args:
            name: Event name.
            payload: Event payload dictionary or Payload instance.

        Returns:
            Self instance for chaining.
        """
        self[name] = (
            payload if isinstance(payload, Payload) else Payload(payload or {})
        )
        return self

    def event(self, name: str, /, **payload: Any) -> Self:
        """
        Convenience method for creating an event with keyword arguments.

        Example
        -------
        >>> events.event("saved", id=10)
        >>> events.event("refreshTable")
        """
        # If no kwargs are passed, pass None to preserve empty dictionary initialization
        return self.add(name, payload if payload else None)

    def merge(self, other: Event) -> Self:
        """
        Merge another event payload into this one.

        Existing events with the same name are overwritten.
        """
        self.update(other.to_dict() if hasattr(other, "to_dict") else other)
        return self

    def remove(self, name: str) -> Self:
        """
        Remove an event by name. Missing events are safely ignored.
        """
        self.pop(name, None)
        return self

    def clear(self) -> Self:
        """
        Remove all registered events.
        """
        super().clear()
        return self

    @property
    def empty(self) -> bool:
        """Returns True if no events are currently registered."""
        return not self

    def __bool__(self) -> bool:
        """Enables native truthiness checks (e.g., `if events:`)."""
        return len(self) > 0

    def __contains__(self, name: Any) -> bool:
        """Enables containment checks (e.g., `if "saved" in events:`)."""
        return name in self.keys()