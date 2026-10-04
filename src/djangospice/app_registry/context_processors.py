from typing import Any

from django.http import HttpRequest

from djangospice.app_registry.helpers import get_app_context


def app_metadata(request: HttpRequest) -> dict[str, Any]:
    """Django template context processor for the current application."""
    return get_app_context(request).as_dict()
