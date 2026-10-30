import hashlib
from typing import Any, Optional, Sequence
from django.utils.text import slugify

# System Constants
MAX_GROUP_LENGTH: int = 100
HASH_LENGTH: int = 16
SCHEMA_MAX: int = 20
SCOPE_MAX: int = 20


def get_hash(items: Sequence[Any], length: int = HASH_LENGTH) -> str:
    """
    Generates a deterministic, non-cryptographic short hexadecimal hash 
    from a sequence of items.

    Args:
        items (Sequence[Any]): An ordered collection of items to hash.
        length (int, optional): The character length of the returned hash. 
                                Defaults to HASH_LENGTH (16).

    Returns:
        str: A truncated hexadecimal string containing only alphanumerics.
    """
    combined = ":".join(str(item) for item in items)
    return hashlib.sha1(combined.encode("utf-8")).hexdigest()[:length]


def build_group_name(scope: str, identifiers: Optional[Sequence[Any]] = None, schema: str = "public") -> str:
    """
    Creates a deterministic, safe, and valid Django Channels group name.

    The resulting name strictly adheres to Django Channels' naming requirements 
    (only alphanumerics, hyphens, underscores, or periods) and is mathematically 
    guaranteed to stay well under the 100-character limit to prevent hash truncation.

    Args:
        scope (str): The functional domain or context of the channel (e.g., 'chat', 'notifications').
        identifiers (Optional[Sequence[Any]], optional): Unique entity IDs (e.g., user IDs, tenant IDs) 
                                                         used to isolate the group. Defaults to None.
        schema (str, optional): The database schema or tenant scope prefix. Defaults to "public".

    Returns:
        str: A safe, formatted string to be used as a Channels group identifier.
    """
    # Normalize schema string to ensure ASCII/alphanumeric formatting
    clean_schema = slugify(str(schema))[:SCHEMA_MAX] or "public"

    # Normalize scope string
    clean_scope = slugify(str(scope))[:SCOPE_MAX] or "default"

    # Base components of the channel path
    parts = [
        "ws",
        clean_schema,
        clean_scope,
    ]

    # Append deterministic routing identifier if provided
    if identifiers:
        digest = get_hash(identifiers, HASH_LENGTH)
        parts.append(digest)

    name = "_".join(parts)

    # Final guard rail against Django Channels' max character limit
    return name[:MAX_GROUP_LENGTH]