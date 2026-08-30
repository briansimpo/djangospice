from __future__ import annotations

from django.db import models


SEARCHABLE_FIELD_TYPES = (
    models.CharField,
    models.TextField,
    models.EmailField,
    models.SlugField,
)


PREFERRED_SEARCH_FIELDS = (
    "code",
    "name",
    "title",
    "label",
    "number",
    "reference",
    "description",
)


def get_search_fields(model) -> tuple[str, ...]:
    fields_by_name = {
        field.name: field
        for field in model._meta.concrete_fields
        if isinstance(field, SEARCHABLE_FIELD_TYPES)
    }

    fields: list[str] = []

    # Preferred conventional fields first.
    for name in PREFERRED_SEARCH_FIELDS:
        if name in fields_by_name:
            fields.append(name)

    return tuple(fields)