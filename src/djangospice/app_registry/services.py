from __future__ import annotations

from django.db import transaction

from .discovery import AppDiscovery
from .registry import AppRegistry


@transaction.atomic
def sync_apps() -> list:
    """Discover Djangospice apps and synchronize them into the database."""

    metadata = AppDiscovery().discover()

    return AppRegistry().register_many(metadata)
