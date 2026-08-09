from __future__ import annotations
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any, Self, overload

from django.http import HttpRequest

from .component import HTMLComponent


@dataclass(slots=True)
class HTMLFragment(HTMLComponent):
    """
    Represents a renderable HTML fragment.
    HTMLFragments are the building blocks for Components, Widgets, Layouts, etc.
    """
    
    def get_context(self) -> dict[str, Any]:
        ctx = super().get_context()
        ctx["fragment"] = self
        return ctx


class HTMLFragments:
    """
    Collection of template fragments.

    Responsible for managing and rendering Out-of-Band (OOB) fragments.
    """

    def __init__(
        self,
        fragments: Iterable[HTMLFragment] | None = None,
    ) -> None:
        self._items: list[HTMLFragment] = list(fragments or [])

    # ------------------------------------------------------------------
    # Collection API
    # ------------------------------------------------------------------

    def add(self, fragment: HTMLFragment) -> Self:
        """Add a fragment."""
        self._items.append(fragment)
        return self

    def extend(self, *fragments: HTMLFragment) -> Self:
        """Add multiple fragments."""
        self._items.extend(fragments)
        return self

    def remove(self, fragment: HTMLFragment) -> Self:
        """Remove a fragment."""
        self._items.remove(fragment)
        return self

    def clear(self) -> Self:
        """Remove all fragments."""
        self._items.clear()
        return self

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, request: HttpRequest | None = None) -> str:
        """Render every fragment into a combined HTML string."""
        return "".join(
            fragment.render(request=request) for fragment in self._items
        )

    # ------------------------------------------------------------------
    # Pythonic Protocols / Helpers
    # ------------------------------------------------------------------

    @property
    def empty(self) -> bool:
        """Return True if the collection contains no fragments."""
        return not self._items

    def __bool__(self) -> bool:
        return bool(self._items)

    def __iter__(self) -> Iterator[HTMLFragment]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, fragment: Any) -> bool:
        """Support membership checks (e.g., `if fragment in fragments`)."""
        return fragment in self._items

    @overload
    def __getitem__(self, index: int) -> HTMLFragment: ...

    @overload
    def __getitem__(self, index: slice) -> HTMLFragments: ...

    def __getitem__(self, index: int | slice) -> HTMLFragment | HTMLFragments:
        """Support indexing and sequence slicing."""
        if isinstance(index, slice):
            return HTMLFragments(self._items[index])
        return self._items[index]

    def __add__(self, other: Iterable[HTMLFragment]) -> HTMLFragments:
        """Support collection concatenation using the `+` operator."""
        if not isinstance(other, Iterable):
            return NotImplemented
        return HTMLFragments(self._items + list(other))

    def __iadd__(self, other: Iterable[HTMLFragment]) -> Self:
        """Support in-place addition using the `+=` operator."""
        if not isinstance(other, Iterable):
            return NotImplemented
        self._items.extend(other)
        return self

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(count={len(self._items)})"

    def __html__(self) -> str:
        """Allows safe rendering directly inside Django HTML templates without auto-escaping."""
        return self.render()

    def __str__(self) -> str:
        return self.render()