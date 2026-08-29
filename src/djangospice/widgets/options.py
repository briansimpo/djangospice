from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from django.apps import apps
from django.core.exceptions import AppRegistryNotReady
from django.db.models import Model

from .utils import slugify



@dataclass
class WidgetOptions:
    """
    Stores the declarative configuration metadata for a widget.
    Automatically handles smart defaults if values are omitted.
    """
    name: str
    title: str
    app_label: str = "" 
    description: str = ""
    template_name: str = ""
    group: str | None = None
    permission: str | None = None
    enabled: bool = True
    priority: int = 100
    cache_timeout: int | None = None
    lazy: bool = False
    refreshable: bool = False
    refresh_interval: int | None = None
    
    model: type[Model] | None = None
    object_parameter: str = "selected_id"
    objects_parameter: str = "selected_ids"

    @classmethod
    def from_meta(
        cls,
        meta: type | None,
        class_name: str,
        module_path: str,
        class_attrs: dict[str, Any] | None = None,
    ) -> "WidgetOptions":

        kwargs: dict[str, Any] = {}

        if meta:
            for f in fields(cls):
                if hasattr(meta, f.name):
                    kwargs[f.name] = getattr(meta, f.name)

        if class_attrs:
            for f in fields(cls):
                if f.name in class_attrs:
                    kwargs[f.name] = class_attrs[f.name]

        if not kwargs.get("app_label"):
            kwargs["app_label"] = cls._resolve_app_label(
                module_path
            )

        if not kwargs.get("name"):
            kwargs["name"] = slugify(
                class_name
            ) if class_name else ""

        if not kwargs.get("title"):
            kwargs["title"] = (
                kwargs["name"]
                .replace("_", " ")
                .title()
            )

        return cls(**kwargs)

    @classmethod
    def _resolve_app_label(cls, module_path: str) -> str:
        """
        Resolves the Django app label from the widget's module path.
        """
        try:
            for app_config in apps.get_app_configs():
                if module_path.startswith(app_config.name):
                    return app_config.label
        except AppRegistryNotReady:
            # Handle cases where apps aren't fully loaded yet
            pass
        
        parts = module_path.split('.')
        return parts[0] if parts else ""

