# payload.py
from __future__ import annotations

import json
from collections.abc import ItemsView, Iterator, KeysView, MutableMapping, ValuesView
from copy import deepcopy
from typing import Any, Self

from .serializer import serialize


class Payload(MutableMapping[str, Any]):
    __slots__ = ("_data",)

    def __init__(self, data: dict[str, Any] | None = None, /, **kwargs: Any) -> None:
        object.__setattr__(self, "_data", {})
        if data:
            self.update(data)
        if kwargs:
            self.update(kwargs)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if isinstance(value, dict) and not isinstance(value, Payload):
            self._data[key] = Payload(value)
        elif isinstance(value, (list, tuple, set)):
            container_type = type(value)
            self._data[key] = container_type(
                Payload(v) if isinstance(v, dict) and not isinstance(v, Payload) else v 
                for v in value
            )
        else:
            self._data[key] = value

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._data[name]
        except KeyError as exc:
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'") from exc

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_data":
            object.__setattr__(self, name, value)
        else:
            self[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self._data[name]
        except KeyError as exc:
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'") from exc

    def to_dict(self) -> dict[str, Any]:
        return serialize(self._data)

    def to_json(self, **kwargs: Any) -> str:
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(data)

    @classmethod
    def from_json(cls, data: str) -> Self:
        return cls(json.loads(data))

    def copy(self) -> Self:
        return type(self)(deepcopy(self.to_dict()))

    def set(self, key: str, value: Any) -> Self:
        self[key] = value
        return self

    def keys(self) -> KeysView[str]: 
        return self._data.keys()
    
    def values(self) -> ValuesView[Any]: 
        return self._data.values()
    
    def items(self) -> ItemsView[str, Any]: 
        return self._data.items()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._data!r})"

    def __bool__(self) -> bool:
        return bool(self._data)

    def __contains__(self, key: object) -> bool:
        return key in self._data