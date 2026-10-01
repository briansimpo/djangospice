from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Self

from .fragments import HTMLFragment


@dataclass(slots=True, kw_only=True)
class OOBEntry:
    fragment: HTMLFragment

    target: str | None = None
    swap: str = "outerHTML"
    select: str | None = None



class OOBList:
    """
    Collection of fragments that should be delivered as HTMX
    out-of-band updates.

    OOBList does not own fragment rendering. HTMLFragment does.
    """

    __slots__ = ("_items",)

    def __init__(
        self,
        items: Iterable[OOBEntry] | None = None,
    ) -> None:
        self._items: list[OOBEntry] = []

        if items is not None:
            self.extend(items)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(
        self,
        fragment: HTMLFragment,
        *,
        target: str | None = None,
        swap: str = "outerHTML",
        select: str | None = None,
    ) -> Self:
        self._items.append(
            OOBEntry(
                fragment=fragment,
                target=target,
                swap=swap,
                select=select,
            )
        )
        return self

    def extend(
        self,
        entries: Iterable[OOBEntry],
    ) -> Self:
        self._items.extend(entries)
        return self

    def clear(self) -> None:
        self._items.clear()

    # ------------------------------------------------------------------
    # Collection
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[OOBEntry]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __bool__(self) -> bool:
        return bool(self._items)

    def __contains__(self, item: object) -> bool:
        return item in self._items

    def __getitem__(
        self,
        index: int | slice,
    ) -> OOBEntry | list[OOBEntry]:
        return self._items[index]

    def __repr__(self) -> str:
        return f"{type(self).__name__}(count={len(self)})"