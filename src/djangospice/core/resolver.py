from __future__ import annotations

import functools
import importlib

from django.apps import apps
from django.core.exceptions import AppRegistryNotReady


@functools.lru_cache(maxsize=1024)
def resolve_class(class_path: str) -> type:
    """
    Optimizes dynamic imports by caching resolved Python class paths.
    Prevents repeated disk lookups during heavy recursive deserialization.
    """
    module_name, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def get_app_label(module_path: str) -> str:
    """
    Safely resolves the Django app label from a module path.
    Immune to AppRegistryNotReady exceptions during early module loads.
    """
    try:
        app_config = apps.get_containing_app_config(module_path)
        if app_config:
            return app_config.label
    except AppRegistryNotReady:
        pass
