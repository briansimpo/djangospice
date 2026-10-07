from __future__ import annotations

import os
from logging import getLogger
from typing import ClassVar

from django.apps import AppConfig as BaseAppConfig
from django.templatetags.static import static

from djangospice.urls import get_valid_url
from .module import Module
from .metadata import Dependency, Permission


logger = getLogger(__name__)


class AppConfig(BaseAppConfig):
    """Base configuration for Djangospice applications."""

    default = False

    app_key: ClassVar[str | None] = None
    app_name: ClassVar[str | None] = None
    app_version: ClassVar[str | None] = None
    app_package: ClassVar[str | None] = None
    app_description: ClassVar[str] = ""
    app_author: ClassVar[str] = ""
    app_icon: ClassVar[str | None] = None
    app_url: ClassVar[str | None] = None
    app_homepage: ClassVar[str | None] = None
    app_dependencies: ClassVar[tuple[Dependency, ...]] = ()
    app_permissions: ClassVar[tuple[Permission, ...]] = ()

    namespace: ClassVar[str | None] = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Automatically make concrete configurations discoverable.
        cls.default = True

        cls._configure_namespace()
        cls._configure_verbose_name()
        cls._configure_app_url()
        cls._configure_app_icon()

    @classmethod
    def _configure_namespace(cls) -> None:
        """Automatically determine the application namespace."""
        namespace = cls.__dict__.get("namespace")

        if isinstance(namespace, str) and namespace.strip():
            cls.namespace = namespace.strip().strip(":")
            return

        label = cls.__dict__.get("label")

        if isinstance(label, str) and label.strip():
            cls.namespace = label.strip()
            return

        app_path = cls.__dict__.get("name")

        if isinstance(app_path, str) and app_path.strip():
            cls.namespace = app_path.rsplit(".", 1)[-1].strip()
            return

        cls.namespace = cls.__name__.removesuffix("Config").lower()

    @classmethod
    def _configure_verbose_name(cls) -> None:
        """Automatically determine the application's display name."""
        if "verbose_name" in cls.__dict__:
            return

        app_name = cls.__dict__.get("app_name")

        if isinstance(app_name, str) and app_name.strip():
            cls.verbose_name = app_name.strip()
            return

        cls.verbose_name = cls._humanize(
            cls.namespace or cls.__name__.removesuffix("Config")
        )

    @classmethod
    def _configure_app_url(cls) -> None:
        """Automatically determine the application's URL."""
        url = cls.__dict__.get("app_url")

        if url:
            cls.app_url = cls._get_valid_url(url)
            return

        if cls.namespace:
            cls.app_url = cls._get_valid_url(f"/{cls.namespace}")

    @classmethod
    def _configure_app_icon(cls) -> None:
        """Automatically determine the application's icon URL."""
        icon = cls.__dict__.get("app_icon")

        if not icon:
            cls.app_icon = f"/static/{cls.namespace}/icon.png"
            return

        if icon.startswith("/static/"):
            cls.app_icon = icon
            return

        if "/" in icon or "\\" in icon:
            cls.app_icon = f"/static/{icon.replace('\\', '/')}"
            return

        cls.app_icon = f"/static/{cls.namespace}/{icon}"

    @classmethod
    def _get_icon_path(cls, icon: str) -> str:
        """
        Return the static asset path for the application icon.

        This does not resolve the path through Django's staticfiles
        system and is therefore safe during application import.
        """
        if not icon:
            icon = "icon.png"

        if "/" in icon or "\\" in icon:
            return icon.replace("\\", "/")

        return os.path.join(
            cls.namespace,
            icon,
        ).replace("\\", "/")

    @classmethod
    def get_icon_url(cls) -> str:
        """
        Resolve the application's icon path to its static URL.

        This method should only be called after Django has initialized
        its application registry.
        """
        return static(cls.app_icon or cls._get_icon_path("icon.png"))

    @staticmethod
    def _get_valid_url(url: str) -> str | None:
        """Validate and return a properly formatted URL."""
        return get_valid_url(url) if url else None

    @staticmethod
    def _humanize(value: str) -> str:
        """Convert an identifier into a human-readable name."""
        return value.replace("_", " ").replace("-", " ").title()

    def has_app_key(self) -> bool:
        """Return whether this application declares a registry key."""
        return isinstance(self.app_key, str) and bool(self.app_key.strip())

    def load_module(self, module):
        Module.discover(module)
