from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.apps import apps
from django.http import HttpRequest



@dataclass(frozen=True, slots=True)
class AppContext:
    """Current Djangospice application context for a request."""

    app: Any | None = None
    app_name: str | None = None
    app_label: str | None = None
    app_verbose: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "app": self.app,
            "app_name": self.app_name,
            "app_label": self.app_label,
            "app_verbose": self.app_verbose,
        }


def get_current_app(request: HttpRequest):
    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match is None or not resolver_match.app_name:
        return None

    try:
        return apps.get_app_config(resolver_match.app_name)
    except LookupError:
        return None


def get_app_context(request: HttpRequest) -> AppContext:
    app = get_current_app(request)
    if app is None:
        return AppContext()

    return AppContext(
        app=app,
        app_name=app.name,
        app_label=app.label,
        app_verbose=app.verbose_name,
    )
