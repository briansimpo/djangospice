from typing import Any

from django.http import HttpRequest

from .helpers import get_app_metadata


def site_metadata(request: HttpRequest) -> dict[str, Any]:
    """Django template context processor for the current application."""
    return get_app_metadata(request).as_dict()
