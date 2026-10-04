from __future__ import annotations

import logging

from django.dispatch import receiver
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)


@receiver(post_migrate,dispatch_uid="register_installed_apps")
def register_installed_apps(sender, using: str, **kwargs) -> None:
    """Register discovered Djangospice apps after registry migrations."""

    if sender.label != "app_registry":
        return

    # Import lazily because this handler only needs the registry
    # service after Django has completed the registry migrations.
    from .services import sync_apps

    try:
        result = sync_apps()
        logger.info(
            "Synchronized installed Djangospice apps: %s",
            len(result),
        )
    except Exception:
        logger.exception(
            "Failed to synchronize installed Djangospice apps "
            "after app_registry migrations."
        )
        raise