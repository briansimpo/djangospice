
from __future__ import annotations

from typing import Any


# Options whose declarations should be combined.
MERGED_META_OPTIONS = {
    "lookups": "field_name",
    "inlines": "relation",
}


def get_meta_options(meta, bases) -> dict[str, Any]:
    """
    Collect inherited Meta options and apply child overrides.

    Child Meta attributes take precedence over inherited attributes.
    """
    options = {}

    # Collect Meta classes from base forms in MRO order.
    for base in reversed(bases):
        base_meta = getattr(base, "Meta", None)

        if base_meta is None:
            continue

        for key, value in vars(base_meta).items():
            if key.startswith("_"):
                continue

            options[key] = value

    # Apply the child Meta class.
    if meta is not None:
        for key, value in vars(meta).items():
            if key.startswith("_"):
                continue

            if key in MERGED_META_OPTIONS:
                options[key] = merge_meta_items(
                    options.get(key, ()),
                    value,
                    MERGED_META_OPTIONS[key],
                )
            else:
                options[key] = value

    return options


def merge_meta_items(parent, child, identity):
    """
    Merge configuration declarations by their identity.

    Child declarations replace inherited declarations with the
    same identity while preserving their original order.
    """
    result = list(parent or ())

    for item in child or ():
        key = getattr(item, identity, None)

        if key is None:
            result.append(item)
            continue

        result = [
            existing
            for existing in result
            if getattr(existing, identity, None) != key
        ]

        result.append(item)

    return tuple(result)
