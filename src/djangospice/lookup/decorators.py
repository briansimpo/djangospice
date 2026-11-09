from __future__ import annotations

from typing import Any

from django.db import models

from .definition import LookupDefinition
from .registry import lookup_registry


def lookup(model: type[models.Model] | models.QuerySet | None = None, **kwargs: Any) -> LookupDefinition:
    """
    Register a Django model or queryset as a lookup.

    The lookup identity is derived from the queryset's model
    or the supplied model class.
    """
    if isinstance(model, models.QuerySet):
        kwargs["queryset"] = model
    elif model is not None:
        kwargs["model"] = model

    definition = LookupDefinition(**kwargs)

    return lookup_registry.register(definition)