
from __future__ import annotations

from functools import lru_cache
from pathlib import PurePosixPath
from django.apps import AppConfig, apps
from django.contrib.staticfiles import finders


class Assets:
    """
    Automatic static asset discovery for Djangospice apps
    and independently installed extensions.

    Convention:
        static/<app_label>/css/*.css
        static/<app_label>/js/*.js
    """

    TYPES = ("css", "js")

    @classmethod
    def get_apps(cls) -> list[AppConfig]:
        """
        Return installed Djangospice apps and extensions.
        """
        return [
            config
            for config in apps.get_app_configs()
            if getattr(config, "djangospice_app", False) is True
        ]

    @staticmethod
    def get_app(module: str) -> AppConfig | None:
        """
        Resolve an app by Django label or Python package name.
        """
        for config in apps.get_app_configs():
            if module in (config.label, config.name):
                return config

        return None

    @classmethod
    def get_prefix(cls, module: str | AppConfig) -> str:
        """
        Resolve a module to its static asset namespace.
        """
        if isinstance(module, AppConfig):
            return module.label

        config = cls.get_app(module)

        if config is not None:
            return config.label

        return module.strip("/").replace("\\", "/")

    @staticmethod
    @lru_cache(maxsize=128)
    def _discover(prefix: str) -> dict[str, tuple[str, ...]]:
        assets = {
            asset_type: set()
            for asset_type in Assets.TYPES
        }

        for finder in finders.get_finders():
            for asset_path, storage in finder.list(ignore_patterns=[]):
                asset_path = asset_path.replace("\\", "/")

                if not asset_path.startswith(f"{prefix}/"):
                    continue

                relative = PurePosixPath(asset_path).relative_to(prefix)

                if len(relative.parts) < 2:
                    continue

                if any(part.startswith("_") for part in relative.parts):
                    continue

                asset_type = relative.parts[0]

                if asset_type not in Assets.TYPES:
                    continue

                if relative.suffix.lower() != f".{asset_type}":
                    continue

                assets[asset_type].add(asset_path)

        return {
            key: tuple(sorted(value))
            for key, value in assets.items()
        }

    @classmethod
    def get_assets(
        cls,
        module: str | AppConfig,
        asset_type: str | None = None,
    ) -> list[str] | dict[str, list[str]]:
        """
        Get discovered assets for a specific app.
        """
        prefix = cls.get_prefix(module)
        assets = cls._discover(prefix)

        if asset_type:
            return list(assets.get(asset_type, ()))

        return {
            key: list(value)
            for key, value in assets.items()
        }

    @classmethod
    def get_apps_assets(
        cls,
        asset_type: str | None = None,
    ) -> dict[str, list[str]]:
        """
        Discover assets from all installed Djangospice apps.

        Returns:
            {
                "notification": {
                    "css": [...],
                    "js": [...],
                }
            }
        """
        result = {}

        for config in cls.get_apps():
            assets = cls.get_assets(config)

            if asset_type:
                result[config.label] = assets.get(asset_type, [])
            else:
                result[config.label] = assets

        return result

    @classmethod
    def get_asset_path(
        cls,
        module: str | AppConfig,
        asset_type: str,
        name: str | None = None,
    ) -> str | None:
        """
        Resolve an individual asset path.

        If name is omitted, return the asset only when
        exactly one matching asset exists.
        """
        if asset_type not in cls.TYPES:
            return None

        assets = cls.get_assets(module, asset_type)

        if name:
            matches = [
                asset
                for asset in assets
                if PurePosixPath(asset).name == name
            ]

            return matches[0] if len(matches) == 1 else None

        return assets[0] if len(assets) == 1 else None

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear discovered asset cache.
        """
        cls._discover.cache_clear()
