from __future__ import annotations

import dataclasses
import functools
import importlib
import types
import uuid
import logging
from collections.abc import Mapping
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from django.db import models
from django.db.models import QuerySet
from rest_framework.serializers import ModelSerializer

from .references import ModelReference, CollectionReference

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1024)
def resolve_class(class_path: str) -> type:
    """
    Optimizes dynamic imports by caching resolved Python class paths.
    Prevents repeated disk lookups during heavy recursive deserialization.
    """
    module_name, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def serialize(value: Any) -> Any:
    """
    Recursively serializes database models, querysets, serializable objects,
    Payloads, DTOs, and Python primitives into clean, JSON-compatible payloads.
    """
    # 1. Block unsupported execution/runtime states
    if isinstance(value, (types.FunctionType, types.MethodType, types.ModuleType, types.GeneratorType, type)):
        raise TypeError(f"Object of type {type(value).__name__} is not serializable.")

    # 2. Return native JSON primitives immediately
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    # 3. Handle Framework & Custom Classes (Serializable, Payload, Django Models)
    if hasattr(value, "to_dict") and callable(getattr(value, "to_dict")):
        return value.to_dict()

    # Convert Models and Querysets directly to Reference Representations
    if isinstance(value, models.Model):
        ref = ModelReference.from_model(value)
        return {
            "__type__": "model_reference",
            "app_label": ref.app_label,
            "model_name": ref.model_name,
            "pk": serialize(ref.pk),
        }

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

    # 4. Handle Direct Reference instances (if already built)
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

    # 5. Specialized Primitives
    if isinstance(value, (datetime, date, time)):
        return {
            "__type__": "datetime_primitive",
            "value": value.isoformat(),
            "kind": value.__class__.__name__
        }
    if isinstance(value, Decimal):
        return {"__type__": "decimal_primitive", "value": str(value)}
    if isinstance(value, uuid.UUID):
        return {"__type__": "uuid_primitive", "value": str(value)}
    
    # Explicitly catch Exceptions (since they don't have standard dictionary states)
    if isinstance(value, BaseException):
        return {
            "__type__": "exception_primitive",
            "class_path": f"{value.__class__.__module__}.{value.__class__.__name__}",
            "message": str(value)
        }

    # 6. Django Serializers & Dataclasses
    if isinstance(value, ModelSerializer):
        return value.data

    # Check if it is a Payload instance
    if value.__class__.__name__ == "Payload":
        return {k: serialize(v) for k, v in value.items()}

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            "__type__": "dataclass",
            "class_path": f"{value.__class__.__module__}.{value.__class__.__name__}",
            "data": {f.name: serialize(getattr(value, f.name)) for f in dataclasses.fields(value)}
        }

    # 7. Standard Collections (Traversed Recursively)
    if isinstance(value, list):
        return [serialize(v) for v in value]
    if isinstance(value, tuple):
        return {"__type__": "tuple", "data": [serialize(v) for v in value]}
    if isinstance(value, set):
        return {"__type__": "set", "data": [serialize(v) for v in value]}
    if isinstance(value, Mapping):
        return {str(k): serialize(v) for k, v in value.items()}

    # 8. Generic Slotted or Dict-based Custom Python Objects/DTOs
    if hasattr(value, "__class__") and value.__class__.__module__ != "builtins":
        if hasattr(value, "__getstate__"):
            state = value.__getstate__()
        elif hasattr(value, "__dict__"):
            state = value.__dict__
        elif hasattr(value, "__slots__"):
            slots = value.__slots__
            if isinstance(slots, str):
                slots = [slots]
            state = {slot: getattr(value, slot) for slot in slots if hasattr(value, slot)}
        else:
            state = {}

        return {
            "__type__": "python_object",
            "class_path": f"{value.__class__.__module__}.{value.__class__.__name__}",
            "state": serialize(state)
        }

    return value


def deserialize(value: Any) -> Any:
    """
    Reconstructs original datatypes, resolving database models, deserializing
    complex nested DTOs, and mapping structures based on hints.
    """
    if isinstance(value, dict):
        val_type = value.get("__type__")

        if not val_type:
            return {k: deserialize(v) for k, v in value.items()}

        # 1. Resolve Django Models & Collections
        if val_type == "model_reference":
            ref = ModelReference(
                app_label=value["app_label"],
                model_name=value["model_name"],
                pk=deserialize(value["pk"]),
            )
            return ref.resolve()

        if val_type == "collection_reference":
            ref = CollectionReference(
                app_label=value["app_label"],
                model_name=value["model_name"],
                pks=tuple(deserialize(pk) for pk in value["pks"]),
                ordered=value["ordered"],
            )
            return ref.resolve()

        # 2. Reconstruct Specialized Primitives
        if val_type == "datetime_primitive":
            raw_val = value["value"]
            kind = value["kind"]
            if kind == "datetime":
                return datetime.fromisoformat(raw_val)
            if kind == "date":
                return date.fromisoformat(raw_val)
            if kind == "time":
                return time.fromisoformat(raw_val)

        if val_type == "decimal_primitive":
            return Decimal(value["value"])

        if val_type == "uuid_primitive":
            return uuid.UUID(value["value"])

        if val_type == "exception_primitive":
            try:
                exc_cls = resolve_class(value["class_path"])
                return exc_cls(value["message"])
            except Exception:
                # Fallback if custom Exception class was deleted/renamed
                return Exception(value["message"])

        # 3. Reconstruct Base Python Collections
        if val_type == "tuple":
            return tuple(deserialize(v) for v in value["data"])

        if val_type == "set":
            return {deserialize(v) for v in value["data"]}

        # 4. Reconstruct Standard Dataclasses/DTOs (With Schema Drift Protection)
        if val_type == "dataclass":
            cls = resolve_class(value["class_path"])
            raw_data = {k: deserialize(v) for k, v in value["data"].items()}
            
            # Prevent crashes if fields were added/removed between queue and execution
            allowed_fields = {f.name for f in dataclasses.fields(cls)}
            filtered_data = {k: v for k, v in raw_data.items() if k in allowed_fields}
            
            missing_fields = allowed_fields - filtered_data.keys()
            if missing_fields:
                logger.warning(
                    f"Reconstructing dataclass '{cls.__name__}' with missing fields "
                    f"from payload: {missing_fields}. Default values or None will be used."
                )

            return cls(**filtered_data)

        # 5. Reconstruct Generic Custom Python Objects
        if val_type == "python_object":
            cls = resolve_class(value["class_path"])
            obj = cls.__new__(cls)
            deserialized_state = deserialize(value["state"])

            if hasattr(obj, "__setstate__"):
                obj.__setstate__(deserialized_state)
            else:
                for k, v in deserialized_state.items():
                    setattr(obj, k, v)
            return obj

    elif isinstance(value, list):
        return [deserialize(v) for v in value]

    return value