
from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import MISSING, fields, is_dataclass
from typing import Any, TypeVar

from .serializer import (
    deserialize,
    serialize,
    construct_dataclass,
)

T = TypeVar("T", bound="Serializable")


class Serializable:
    """
    Base class for mutable serializable dataclasses.

    Subclasses must be decorated with @dataclass.
    """

    __djangospice_serializable__ = True

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    @classmethod
    def _validate_class(cls) -> None:
        if not is_dataclass(cls):
            raise TypeError(
                f"{cls.__name__} must be decorated with @dataclass."
            )

    def _validate(self) -> None:
        if not is_dataclass(self):
            raise TypeError(
                f"{type(self).__name__} must be a dataclass instance."
            )

    @classmethod
    def _field_names(cls) -> set[str]:
        cls._validate_class()
        return {field.name for field in fields(cls)}

    # --------------------------------------------------------
    # Attribute access
    # --------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Get a declared attribute."""

        self._validate()

        if key not in self._field_names():
            return default

        return getattr(self, key)

    def set(
        self,
        key: str | None = None,
        value: Any = None,
        **kwargs: Any,
    ) -> T:
        """
        Set one or multiple declared attributes.

        Examples:
            instance.set("name", "John")
            instance.set(name="John", age=25)
        """

        self._validate()

        updates = {}

        if key is not None:
            updates[key] = value

        updates.update(kwargs)

        valid_fields = self._field_names()

        for attr, attr_value in updates.items():
            if attr not in valid_fields:
                raise AttributeError(
                    f"{type(self).__name__} has no "
                    f"serializable field '{attr}'."
                )

            setattr(self, attr, attr_value)

        return self

    # --------------------------------------------------------
    # Serialization
    # --------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Return a recursively serialized dictionary.

        Nested dataclasses, models, collections and other
        supported values retain their serialization metadata.
        """

        self._validate()

        return {
            field.name: serialize(getattr(self, field.name))
            for field in fields(self)
        }

    def to_json(self, **kwargs: Any) -> str:
        """Serialize this instance into JSON."""

        return json.dumps(self.to_dict(), **kwargs)

    # --------------------------------------------------------
    # Reconstruction
    # --------------------------------------------------------

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """
        Reconstruct an instance from a serialized dictionary.

        Accepts:
            - Ordinary dictionaries
            - Dictionaries containing tagged nested objects
            - Fully tagged serialized dataclass representations
        """

        cls._validate_class()

        if not isinstance(data, dict):
            raise TypeError(
                f"Expected dictionary, got {type(data).__name__}."
            )

        # Support passing the complete tagged representation.
        if data.get("__type__") == "dataclass":
            instance = deserialize(data)

            if not isinstance(instance, cls):
                raise TypeError(
                    f"Expected {cls.__name__}, "
                    f"got {type(instance).__name__}."
                )

            return instance

        # Recursively restore nested values.
        decoded_data = {
            key: deserialize(value)
            for key, value in data.items()
        }

        return construct_dataclass(cls, decoded_data)

    @classmethod
    def from_json(cls: type[T], data: str) -> T:
        """Reconstruct an instance from JSON."""

        return cls.from_dict(json.loads(data))

    # --------------------------------------------------------
    # Object operations
    # --------------------------------------------------------

    def copy(self: T) -> T:
        """Create a deep serialized copy."""

        return type(self).from_dict(self.to_dict())

    def update(self: T, **kwargs: Any) -> T:
        """Update existing declared fields."""

        return self.set(**kwargs)

    def merge(self: T, other: T) -> T:
        """
        Merge another instance into this instance.

        None values are ignored. Dictionaries, lists and sets
        are merged; other values are replaced.
        """

        self._validate()

        if not isinstance(other, type(self)):
            raise TypeError(
                f"Cannot merge {type(other).__name__} "
                f"into {type(self).__name__}."
            )

        for field in fields(self):
            incoming = getattr(other, field.name)

            if incoming is None:
                continue

            current = getattr(self, field.name)

            if isinstance(current, dict) and isinstance(incoming, dict):
                current.update(deepcopy(incoming))

            elif isinstance(current, list) and isinstance(incoming, list):
                current.extend(deepcopy(incoming))

            elif isinstance(current, set) and isinstance(incoming, set):
                current.update(deepcopy(incoming))

            else:
                setattr(self, field.name, deepcopy(incoming))

        return self

    def clear(self: T) -> T:
        """Reset all fields to their defaults."""

        self._validate()

        for field in fields(self):
            if field.default is not MISSING:
                value = deepcopy(field.default)

            elif field.default_factory is not MISSING:
                value = field.default_factory()

            else:
                value = None

            setattr(self, field.name, value)

        return self
