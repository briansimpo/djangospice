
from __future__ import annotations

from importlib import import_module
from typing import Iterable

from django.apps import AppConfig, apps
from django.urls import URLPattern, URLResolver, include, path

from djangospice.package.module import Module


URLPatternType = URLPattern | URLResolver


class Routing:
    """
    Central routing manager for Djangospice applications and extensions.

    Supports automatic discovery and collection of HTTP and
    other URL pattern contributions.
    """

    @staticmethod
    def collect_urlpatterns(module_type: str = "url", attribute: str = "urlpatterns") -> list[URLPatternType]:
        """
        Collect URL patterns from discovered Djangospice modules.
        """
        urlpatterns: list[URLPatternType] = []

        for module in Module.get_modules(module_type):
            patterns = getattr(module, attribute, None)

            if patterns is None:
                continue

            if not isinstance(patterns, (list, tuple)):
                raise TypeError(
                    f"{module}: {attribute} must be a list or tuple."
                )

            urlpatterns.extend(patterns)

        return urlpatterns

    @staticmethod
    def is_djangospice_app(config: AppConfig) -> bool:
        """
        Identify Djangospice applications and extensions.
        """
        return getattr(config, "djangospice_app", False) is True

    @staticmethod
    def import_optional(module_path: str):
        """
        Import an optional URL module.

        Ignore missing optional modules while propagating errors
        originating from dependencies inside existing modules.
        """
        try:
            return import_module(module_path)

        except ModuleNotFoundError as exc:
            missing = exc.name or ""

            if (
                module_path == missing
                or module_path.startswith(f"{missing}.")
            ):
                return None

            raise

    @classmethod
    def build_urlpatterns(cls, app_configs: Iterable[AppConfig] | None = None, attribute: str = "urlpatterns", namespace: bool = True) -> list[URLPatternType]:
        """
        Automatically build URL patterns from installed
        Djangospice applications and extensions.

        Each application is mounted under its Django app label.
        """
        urlpatterns: list[URLPatternType] = []

        if app_configs is None:
            app_configs = apps.get_app_configs()

        for config in app_configs:
            if not cls.is_djangospice_app(config):
                continue

            module_path = f"{config.name}.urls"
            module = cls.import_optional(module_path)

            if module is None:
                continue

            patterns = getattr(module, attribute, None)

            if patterns is None:
                continue

            if not isinstance(patterns, (list, tuple)):
                raise TypeError(
                    f"{config.name}: {attribute} "
                    "must be a list or tuple."
                )

            if not patterns:
                continue

            if namespace:
                urlpatterns.append(
                    path(
                        f"{config.label}/",
                        include((patterns, config.label)),
                    )
                )
            else:
                urlpatterns.append(
                    path(
                        f"{config.label}/",
                        include(patterns),
                    )
                )

        return urlpatterns
