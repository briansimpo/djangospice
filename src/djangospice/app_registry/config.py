from __future__ import annotations

from logging import getLogger
from typing import ClassVar

from django.apps import AppConfig as BaseAppConfig

from djangospice.app_registry.metadata import Dependency, Permission


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

    # Optional application namespace.
    namespace: ClassVar[str | None] = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.default = True

        # Resolve a namespace without accidentally inheriting a value
        # calculated for another configuration class.
        namespace = cls.__dict__.get("namespace")

        if not namespace:
            explicit_label = cls.__dict__.get("label")
            app_name = cls.__dict__.get("name")

            namespace = (
                explicit_label
                or (
                    app_name.rsplit(".", 1)[-1]
                    if isinstance(app_name, str) and app_name
                    else cls.__name__.removesuffix("Config").lower()
                )
            )

        cls.namespace = namespace

    def has_app_key(self) -> bool:
        return isinstance(self.app_key, str) and bool(self.app_key.strip())
