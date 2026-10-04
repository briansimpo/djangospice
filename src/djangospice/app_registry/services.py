from __future__ import annotations

from django.db import transaction

from .discovery import DjangoAppDiscovery
from .registry import app_registry


@transaction.atomic
def sync_apps() -> list:
    """Discover Django apps and synchronize their metadata into the database."""
    return app_registry.register_many(DjangoAppDiscovery().discover())
