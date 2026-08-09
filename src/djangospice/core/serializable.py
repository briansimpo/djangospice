from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import MISSING, fields, is_dataclass
from typing import Any, TypeVar

from djangospice.core.serializer import deserialize, serialize

T = TypeVar("T", bound="Serializable")


class Serializable:
    """
    Base class for mutable serializable dataclasses.
    Subclasses must be decorated with ``@dataclass``.
    """

    @classmethod
    def _validate_class(cls) -> None:
        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be decorated with @dataclass.")

    def _validate(self) -> None:
        if not is_dataclass(self):
            raise TypeError(f"{type(self).__name__} must be a dataclass instance.")

    def to_dict(self) -> dict[str, Any]:
        """Serialize this object recursively."""
        self._validate()
        return {field.name: serialize(getattr(self, field.name)) for field in fields(self)}

    def to_json(self, **kwargs: Any) -> str:
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """Construct an object from a dictionary, mapping known fields recursively."""
        cls._validate_class()
        init_kwargs = {}
        for field in fields(cls):
            if field.name in data:
                init_kwargs[field.name] = deserialize(data[field.name], field.type)
        return cls(**init_kwargs)

    @classmethod
    def from_json(cls: type[T], data: str) -> T:
        return cls.from_dict(json.loads(data))

    def copy(self: T) -> T:
        return type(self).from_dict(self.to_dict())

    def update(self: T, **kwargs: Any) -> T:
        self._validate()
        valid_fields = {field.name for field in fields(self)}
        for key, value in kwargs.items():
            if key in valid_fields:
                setattr(self, key, value)
        return self

    def merge(self: T, other: T) -> T:
        self._validate()
        if not isinstance(other, type(self)):
            raise TypeError(f"Cannot merge {type(other).__name__} into {type(self).__name__}.")

        for field in fields(self):
            incoming = getattr(other, field.name)
            if incoming is None:
                continue

            current = getattr(self, field.name)
            # In-place extension for standard mutable collections
            if isinstance(current, dict) and isinstance(incoming, dict):
                current.update(incoming)
            elif isinstance(current, list) and isinstance(incoming, list):
                current.extend(incoming)
            elif isinstance(current, set) and isinstance(incoming, set):
                current.update(incoming)
            else:
                setattr(self, field.name, deepcopy(incoming))
        return self

    def clear(self: T) -> T:
        self._validate()
        for field in fields(self):
            if field.default is not MISSING:
                setattr(self, field.name, deepcopy(field.default))
            elif field.default_factory is not MISSING:
                setattr(self, field.name, field.default_factory())
            else:
                setattr(self, field.name, None)
        return self