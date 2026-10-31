from __future__ import annotations

import dataclasses
import logging
import math
import types
import uuid

from collections.abc import Mapping
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any

from django.db import models
from django.db.models import QuerySet
from rest_framework.serializers import BaseSerializer

from .references import ModelReference, CollectionReference
from .resolver import resolve_class


logger = logging.getLogger(__name__)


# ============================================================
# Serialization helpers
# ============================================================

def get_class_path(cls: type) -> str:
    """Return the fully qualified Python class path."""
    return f"{cls.__module__}.{cls.__qualname__}"


def serialize_mapping(value: Mapping) -> dict[str, Any]:
    """
    Serialize a mapping.

    JSON object keys must be strings. Reject other keys instead
    of silently converting them and potentially causing collisions.
    """
    result = {}

    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError(
                f"Mapping keys must be strings, got {type(key).__name__}."
            )

        result[key] = serialize(item)

    return result


def serialize_dataclass(value: Any) -> dict[str, Any]:
    """Serialize a dataclass while preserving its class identity."""

    return {
        "__type__": "dataclass",
        "class_path": get_class_path(type(value)),
        "data": {
            field.name: serialize(getattr(value, field.name))
            for field in dataclasses.fields(value)
        },
    }


# ============================================================
# Serialization
# ============================================================

def serialize(value: Any) -> Any:
    """
    Recursively serialize supported Python objects into
    JSON-compatible representations.

    Supported:
        - Native JSON primitives
        - Django models and querysets
        - ModelReference and CollectionReference
        - Datetimes, dates and times
        - Decimal and UUID
        - Enums
        - Exceptions
        - Dataclasses / DTOs
        - Lists, tuples, sets and mappings
        - Explicitly opted-in custom objects
    """

    # 1. Unsupported runtime objects
    if isinstance(
        value,
        (
            types.FunctionType,
            types.MethodType,
            types.ModuleType,
            types.GeneratorType,
            type,
        ),
    ):
        raise TypeError(
            f"Object of type {type(value).__name__} is not serializable."
        )

    # 2. Native JSON primitives
    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("NaN and Infinity are not valid JSON values.")
        return value

    # 3. Django model references
    if isinstance(value, models.Model):
        ref = ModelReference.from_model(value)

        return {
            "__type__": "model_reference",
            "app_label": ref.app_label,
            "model_name": ref.model_name,
            "pk": serialize(ref.pk),
        }

    # 4. Querysets and managers
    if isinstance(value, (QuerySet, models.Manager)):
        queryset = value.all() if isinstance(value, models.Manager) else value

        ref = CollectionReference.from_queryset(queryset)

        return {
            "__type__": "collection_reference",
            "app_label": ref.app_label,
            "model_name": ref.model_name,
            "pks": [serialize(pk) for pk in ref.pks],
            "ordered": ref.ordered,
        }

    # 5. Explicit references
    if isinstance(value, ModelReference):
        return {
            "__type__": "model_reference",
            "app_label": value.app_label,
            "model_name": value.model_name,
            "pk": serialize(value.pk),
        }

    if isinstance(value, CollectionReference):
        return {
            "__type__": "collection_reference",
            "app_label": value.app_label,
            "model_name": value.model_name,
            "pks": [serialize(pk) for pk in value.pks],
            "ordered": value.ordered,
        }

    if isinstance(value, Enum):
        return {
            "__type__": "enum",
            "class_path": get_class_path(type(value)),
            "value": serialize(value.value),
        }

    # 6. Specialized primitives
    if isinstance(value, datetime):
        return {
            "__type__": "datetime_primitive",
            "kind": "datetime",
            "value": value.isoformat(),
        }

    if isinstance(value, date):
        return {
            "__type__": "datetime_primitive",
            "kind": "date",
            "value": value.isoformat(),
        }

    if isinstance(value, time):
        return {
            "__type__": "datetime_primitive",
            "kind": "time",
            "value": value.isoformat(),
        }

    if isinstance(value, Decimal):
        return {
            "__type__": "decimal_primitive",
            "value": str(value),
        }

    if isinstance(value, uuid.UUID):
        return {
            "__type__": "uuid_primitive",
            "value": str(value),
        }

    if isinstance(value, BaseException):
        return {
            "__type__": "exception_primitive",
            "class_path": get_class_path(type(value)),
            "message": str(value),
        }

    # 7. Django REST Framework serializers
    if isinstance(value, BaseSerializer):
        return serialize(value.data)

    # 8. Dataclasses / DTOs
    # Must come before to_dict() to preserve their class identity.
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return serialize_dataclass(value)

    # 9. Standard collections
    if isinstance(value, list):
        return [serialize(item) for item in value]

    if isinstance(value, tuple):
        return {
            "__type__": "tuple",
            "data": [serialize(item) for item in value],
        }

    if isinstance(value, (set, frozenset)):
        return {
            "__type__": "frozenset" if isinstance(value, frozenset) else "set",
            "data": [serialize(item) for item in value],
        }

    if isinstance(value, Mapping):
        return serialize_mapping(value)

    # 10. Explicitly serializable custom objects
    #
    # Opt-in by defining:
    # __djangospice_serializable__ = True
    #
    # The class must implement to_dict() and from_dict().
    if getattr(type(value), "__djangospice_serializable__", False):

        if not callable(getattr(value, "to_dict", None)):
            raise TypeError(
                f"{type(value).__name__} must implement to_dict()."
            )

        return {
            "__type__": "serializable_object",
            "class_path": get_class_path(type(value)),
            "data": serialize(value.to_dict()),
        }

    # 11. Unsupported objects
    raise TypeError(
        f"Object of type {type(value).__name__} is not serializable. "
        "Use a supported DTO or explicitly implement the serialization protocol."
    )


# ============================================================
# Deserialization helpers
# ============================================================

def deserialize_model_reference(value: dict[str, Any]) -> Any:
    ref = ModelReference(
        app_label=value["app_label"],
        model_name=value["model_name"],
        pk=deserialize(value["pk"]),
    )

    return ref.resolve()


def deserialize_collection_reference(value: dict[str, Any]) -> Any:
    ref = CollectionReference(
        app_label=value["app_label"],
        model_name=value["model_name"],
        pks=tuple(deserialize(pk) for pk in value["pks"]),
        ordered=value["ordered"],
    )

    return ref.resolve()


def deserialize_datetime(value: dict[str, Any]) -> Any:
    raw = value["value"]
    kind = value["kind"]

    constructors = {
        "datetime": datetime.fromisoformat,
        "date": date.fromisoformat,
        "time": time.fromisoformat,
    }

    constructor = constructors.get(kind)

    if constructor is None:
        raise ValueError(f"Unsupported datetime kind: {kind}")

    return constructor(raw)


def deserialize_exception(value: dict[str, Any]) -> BaseException:
    message = value["message"]

    try:
        cls = resolve_class(value["class_path"])

        if not isinstance(cls, type) or not issubclass(cls, BaseException):
            raise TypeError("Resolved class is not an exception.")

        return cls(message)

    except Exception:
        logger.warning(
            "Could not reconstruct exception class %s. Using Exception.",
            value["class_path"],
        )
        return Exception(message)


def deserialize_dataclass(value: dict[str, Any]) -> Any:
    cls = resolve_class(value["class_path"])

    if not dataclasses.is_dataclass(cls):
        raise TypeError(
            f"Resolved class {cls.__name__} is not a dataclass."
        )

    raw_data = {
        key: deserialize(item)
        for key, item in value["data"].items()
    }

    return construct_dataclass(cls, raw_data)


def construct_dataclass(cls: type, data: dict[str, Any]) -> Any:
    """Construct a dataclass while supporting schema evolution."""

    fields = dataclasses.fields(cls)

    init_fields = {
        field.name: field
        for field in fields
        if field.init
    }

    filtered_data = {
        key: item
        for key, item in data.items()
        if key in init_fields
    }

    missing_required = {
        name
        for name, field in init_fields.items()
        if (
            name not in filtered_data
            and field.default is dataclasses.MISSING
            and field.default_factory is dataclasses.MISSING
        )
    }

    if missing_required:
        logger.warning(
            "Reconstructing %s with missing required fields: %s",
            cls.__name__,
            sorted(missing_required),
        )

    instance = cls(**filtered_data)

    # Restore non-init fields when they were included in the payload.
    for field in fields:
        if field.init or field.name not in data:
            continue

        object.__setattr__(
            instance,
            field.name,
            data[field.name],
        )

    return instance


def deserialize_serializable_object(value: dict[str, Any]) -> Any:
    cls = resolve_class(value["class_path"])

    if not getattr(cls, "__djangospice_serializable__", False):
        raise TypeError(
            f"{cls.__name__} is not an approved serializable class."
        )

    return cls.from_dict(value["data"])


def deserialize_enum(value: dict[str, Any]) -> Any:
    cls = resolve_class(value["class_path"])

    if not isinstance(cls, type) or not issubclass(cls, Enum):
        raise TypeError("Resolved class is not an Enum.")

    return cls(deserialize(value["value"]))


# ============================================================
# Deserialization
# ============================================================

def deserialize(value: Any) -> Any:
    """Recursively reconstruct serialized Python objects."""

    if isinstance(value, list):
        return [deserialize(item) for item in value]

    if not isinstance(value, dict):
        return value

    val_type = value.get("__type__")

    # Ordinary dictionary
    if val_type is None:
        return {
            key: deserialize(item)
            for key, item in value.items()
        }

    # Tagged representations
    handlers = {
        "model_reference": deserialize_model_reference,
        "collection_reference": deserialize_collection_reference,
        "datetime_primitive": deserialize_datetime,
        "decimal_primitive": lambda v: Decimal(v["value"]),
        "uuid_primitive": lambda v: uuid.UUID(v["value"]),
        "exception_primitive": deserialize_exception,
        "enum": deserialize_enum,
        "tuple": lambda v: tuple(deserialize(x) for x in v["data"]),
        "set": lambda v: {deserialize(x) for x in v["data"]},
        "frozenset": lambda v: frozenset(
            deserialize(x) for x in v["data"]
        ),
        "dataclass": deserialize_dataclass,
        "serializable_object": deserialize_serializable_object,
    }

    handler = handlers.get(val_type)

    if handler is None:
        raise ValueError(
            f"Unsupported serialized type: {val_type}"
        )

    return handler(value)
