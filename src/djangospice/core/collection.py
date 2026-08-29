from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import Generic, TypeVar

from .entity import Entity
from .object import Object


T = TypeVar("T")
E = TypeVar("E", bound=Entity)
V = TypeVar("V", bound=Object)


def normalize(items: T | Iterable[T]) -> list[T]:
    if isinstance(items, Iterable) and not isinstance(items, (str, bytes)):
        return list(items)

    return [items]


class BaseCollection(Generic[T]):
    """
    Common collection behavior.
    """

    _items: Sequence[T]

    def first(self) -> T | None:
        return self._items[0] if self._items else None

    def last(self) -> T | None:
        return self._items[-1] if self._items else None

    def is_empty(self) -> bool:
        return not self._items

    def index(self, item: T) -> int:
        return self._items.index(item)

    def contains(self, item: T) -> bool:
        return item in self

    def contains_all(self, items: Iterable[T]) -> bool:
        return all(item in self for item in items)

    def contains_any(self, items: Iterable[T]) -> bool:
        return any(item in self for item in items)

    def intersects(self, items: Iterable[T]) -> bool:
        return self.contains_any(items)

    def filter(
        self,
        predicate: Callable[[T], bool],
    ) -> BaseCollection[T]:
        return type(self)(
            item
            for item in self
            if predicate(item)
        )

    def find(
        self,
        predicate: Callable[[T], bool],
    ) -> T | None:
        return next(
            (item for item in self if predicate(item)),
            None,
        )

    def any(
        self,
        predicate: Callable[[T], bool] | None = None,
    ) -> bool:
        return (
            bool(self)
            if predicate is None
            else any(predicate(item) for item in self)
        )

    def all(self, predicate: Callable[[T], bool]) -> bool:
        return all(predicate(item) for item in self)

    def count(
        self,
        predicate: Callable[[T], bool] | None = None,
    ) -> int:
        return (
            len(self)
            if predicate is None
            else sum(predicate(item) for item in self)
        )

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def __contains__(self, item: T) -> bool:
        return item in self._items

    def __bool__(self) -> bool:
        return bool(self._items)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({len(self)} items)"


class Collection(BaseCollection[T]):
    """
    Generic mutable collection.
    """

    def __init__(
        self,
        items: T | Iterable[T] | None = None,
        *args: T,
    ) -> None:
        self._items = []

        if items is not None:
            self._items.extend(normalize(items))

        self._items.extend(args)

    def add(self, item: T) -> None:
        self._items.append(item)

    def extend(self, items: Iterable[T]) -> None:
        self._items.extend(items)

    def remove(self, item: T) -> None:
        self._items.remove(item)

    def clear(self) -> None:
        self._items.clear()

    def copy(self) -> Collection[T]:
        return type(self)(self._items)

    def sort(
        self,
        *,
        key=None,
        reverse: bool = False,
    ) -> None:
        self._items.sort(key=key, reverse=reverse)


class ImmutableCollection(BaseCollection[T]):
    """
    Generic immutable collection.
    """

    __slots__ = ("_items",)

    def __init__(
        self,
        items: T | Iterable[T] | None = None,
        *args: T,
    ) -> None:
        normalized = normalize(items) if items is not None else []
        normalized.extend(args)

        self._items = tuple(normalized)


class EntityCollection(Collection[E]):
    """
    Collection of entities.
    """

    @classmethod
    def from_iterable(
        cls,
        items: Iterable[E],
    ) -> EntityCollection[E]:
        return cls(items)


class ObjectCollection(Collection[V]):
    """
    Collection of value objects.
    """

    @classmethod
    def from_iterable(
        cls,
        items: Iterable[V],
    ) -> ObjectCollection[V]:
        return cls(items)


class ImmutableEntityCollection(
    ImmutableCollection[E],
    Generic[E],
):
    """
    Immutable collection of entities.
    """

    @classmethod
    def from_iterable(
        cls,
        items: Iterable[E],
    ) -> ImmutableEntityCollection[E]:
        return cls(items)


class ImmutableObjectCollection(
    ImmutableCollection[V],
    Generic[V],
):
    """
    Immutable collection of value objects.
    """

    @classmethod
    def from_iterable(
        cls,
        items: Iterable[V],
    ) -> ImmutableObjectCollection[V]:
        return cls(items)