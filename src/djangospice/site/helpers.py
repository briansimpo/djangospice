from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.apps import apps
from django.http import HttpRequest



@dataclass(frozen=True, slots=True)
class AppMetadata:
    """Current Djangospice application context for a request."""

    app: Any | None = None
    app_name: str | None = None
    app_label: str | None = None
    app_title: str | None = None


    def as_dict(self) -> dict[str, Any]:
        return {
            "app": self.app,
            "app_name": self.app_name,
            "app_label": self.app_label,
            "app_title": self.app_title,
        }


def get_current_app(request: HttpRequest):
    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match is None or not resolver_match.app_name:
        return None

    try:
        return apps.get_app_config(resolver_match.app_name)
    except LookupError:
        return None


def get_app_metadata(request: HttpRequest) -> AppMetadata:
    app = get_current_app(request)
    if app is None:
        return AppMetadata()

    return AppMetadata(
        app=app,
        app_name=app.name,
        app_label=app.label,
        app_title=app.verbose_name,
    )

