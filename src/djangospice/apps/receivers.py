from __future__ import annotations

import logging

from django.dispatch import receiver
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)


@receiver(post_migrate,dispatch_uid="register_installed_apps")
def register_installed_apps(sender, using: str, **kwargs) -> None:
    """Register discovered Djangospice apps after registry migrations."""

    if sender.label != "apps":
        return

    from .register import register_apps

    try:
        result = register_apps()
        logger.info(
            "Synchronized installed Djangospice apps: %s",
            len(result),
        )
    except Exception:
        logger.exception(
            "Failed to synchronize installed Djangospice apps "
            "after apps migrations."
        )
        raise