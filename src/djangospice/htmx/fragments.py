from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import Any, Self, overload

from django.http import HttpRequest
from django.utils.safestring import SafeString, mark_safe

from .component import HTMLComponent


@dataclass(slots=True, kw_only=True)
class HTMLFragment(HTMLComponent):
    template_name: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    html: str | None = None

    def get_context(self) -> dict[str, Any]:
        return dict(self.context)

    @classmethod
    def from_html(cls, html: str) -> Self:
        return cls(
            html=html,
        )


class HTMLFragments:
    """
    Collection of template fragments.

    Responsible for managing and rendering Out-of-Band (OOB) fragments.
    """

    def __init__(
        self,
        fragments: Iterable[HTMLFragment] | None = None,
    ) -> None:
        self._items: list[HTMLFragment] = []
        if fragments:
            self.extend(fragments)

    # ------------------------------------------------------------------
    # Collection API
    # ------------------------------------------------------------------

    def add(self, fragment: HTMLFragment) -> Self:
        """Add a single fragment."""
        self._items.append(fragment)
        return self

    def extend(self, *fragments: HTMLFragment | Iterable[HTMLFragment]) -> Self:
        """
        Add multiple fragments. Accepts individual HTMLFragment arguments
        or iterables containing fragments.
        """
        for item in fragments:
            if isinstance(item, HTMLFragment):
                self._items.append(item)
            elif isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
                for sub_item in item:
                    if isinstance(sub_item, HTMLFragment):
                        self._items.append(sub_item)
                    else:
                        raise TypeError(
                            f"Expected HTMLFragment, got {type(sub_item).__name__}"
                        )
            else:
                raise TypeError(
                    f"Expected HTMLFragment or Iterable, got {type(item).__name__}"
                )
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

    def render(self, request: HttpRequest | None = None) -> SafeString:
        """Render every fragment into a combined, safe HTML string."""
        rendered = "".join(
            fragment.render(request=request) for fragment in self._items
        )
        return mark_safe(rendered)

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

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, HTMLFragments):
            return self._items == other._items
        if isinstance(other, list):
            return self._items == other
        return False

    @overload
    def __getitem__(self, index: int) -> HTMLFragment: ...

    @overload
    def __getitem__(self, index: slice) -> HTMLFragments: ...

    def __getitem__(self, index: int | slice) -> HTMLFragment | HTMLFragments:
        """Support indexing and sequence slicing."""
        if isinstance(index, slice):
            return HTMLFragments(self._items[index])
        return self._items[index]

    def __add__(self, other: Any) -> HTMLFragments:
        """Support collection concatenation using the `+` operator."""
        if isinstance(other, (str, bytes)) or not isinstance(other, Iterable):
            return NotImplemented
        new_collection = HTMLFragments(self._items)
        new_collection.extend(other)
        return new_collection

    def __iadd__(self, other: Any) -> Self:
        """Support in-place addition using the `+=` operator."""
        if isinstance(other, (str, bytes)) or not isinstance(other, Iterable):
            return NotImplemented
        self.extend(other)
        return self

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(count={len(self._items)})"

    def __html__(self) -> str:
        """Allows safe rendering directly inside Django HTML templates without auto-escaping."""
        return self.render()

    def __str__(self) -> str:
        return self.render()