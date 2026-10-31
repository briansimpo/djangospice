from __future__ import annotations

from django.db import transaction
from djangospice.package.discovery import MetadataDiscovery

from .services import app_service


@transaction.atomic
def register_apps() -> list:
    """Discover Djangospice apps and synchronize them into the database."""

    metadata = MetadataDiscovery().discover()

    return app_service.register_many(metadata)
