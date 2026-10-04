from __future__ import annotations

from django.apps import AppConfig
from djangospice.app_registry.metadata import Permission, Dependency


class DjangospiceConfig(AppConfig):
    app_key: str | None = None

    app_version: str | None = None
    app_package: str | None = None
    app_description: str = ""
    app_author: str = ""
    app_icon: str | None = None
    app_url: str | None = None
    app_homepage: str | None = None

    app_dependencies: tuple[Dependency, ...] = ()
    app_permissions: tuple[Permission, ...] = ()

    namespace: str | None = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # 1. Resolve namespace statically
        # Fallback order: Explicit namespace -> Explicit label -> Module suffix of name
        if cls.namespace is None:
            name = getattr(cls, "name", None)
            fallback_name = name.rsplit(".", 1)[-1] if name else None
            cls.namespace = getattr(cls, "label", None) or fallback_name

        # 2. Sync the label statically
        if getattr(cls, "label", None) is None:
            cls.label = cls.namespace
