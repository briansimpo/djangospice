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

    # 2. Fallback: Parse common Python/Django package conventions
    # e.g., "myproject.apps.billing.jobs" -> ["myproject", "apps", "billing", "jobs"]
    parts = module_path.split(".")
    
    if len(parts) > 1:
        # If 'apps' is in the path, the app name is immediately after it
        if "apps" in parts:
            idx = parts.index("apps")
            if idx + 1 < len(parts):
                return parts[idx + 1]
        
        # Standard root-level app structure (e.g., "billing.jobs" -> "billing")
        return parts[0]

    return "global"