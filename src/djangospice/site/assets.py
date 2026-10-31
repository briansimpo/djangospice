
"""
Djangospice static asset discovery.

Convention:
    static/<module>/css/*.css
    static/<module>/js/*.js
"""

from functools import lru_cache
from pathlib import PurePosixPath

from django.apps import apps
from django.contrib.staticfiles import finders


ASSET_TYPES = ("css", "js")


def _module_prefix(module):
    """Resolve a module name to its static namespace."""
    try:
        config = apps.get_app_config(module)
        module = config.label
    except LookupError:
        pass

    return module.strip("/").replace("\\", "/")


def _discover_assets(module):
    """Discover public CSS and JS assets belonging to a module."""
    prefix = _module_prefix(module)

    assets = {
        "css": [],
        "js": [],
    }

    for finder in finders.get_finders():
        for path, storage in finder.list(ignore_patterns=[]):
            path = path.replace("\\", "/")

            if not path.startswith(f"{prefix}/"):
                continue

            relative = PurePosixPath(path).relative_to(prefix)

            if len(relative.parts) < 2:
                continue

            # Exclude private files and directories.
            if any(part.startswith("_") for part in relative.parts):
                continue

            asset_type = relative.parts[0]

            if asset_type not in ASSET_TYPES:
                continue

            if relative.suffix.lower() != f".{asset_type}":
                continue

            assets[asset_type].append(path)

    for asset_type in ASSET_TYPES:
        assets[asset_type] = sorted(set(assets[asset_type]))

    return assets


@lru_cache(maxsize=128)
def get_assets(module, asset_type=None):
    assets = _discover_assets(_module_prefix(module))

    if asset_type:
        return list(assets.get(asset_type, []))

    return {
        key: list(value)
        for key, value in assets.items()
    }


def get_asset_path(module, asset_type, name=None):
    assets = get_assets(module, asset_type)

    if name:
        matches = [
            path for path in assets
            if PurePosixPath(path).name == name
        ]
        return matches[0] if len(matches) == 1 else None

    return assets[0] if len(assets) == 1 else None


def clear_asset_cache():
    _discover_assets.cache_clear()