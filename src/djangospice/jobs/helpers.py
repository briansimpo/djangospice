from django.apps import apps
from django.core.exceptions import AppRegistryNotReady

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
