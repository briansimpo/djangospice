from __future__ import annotations

from django.http import HttpRequest, HttpResponse

from .registry import RendererRegistry
from .response import Response


def render_response(response: Response, request: HttpRequest) -> HttpResponse:
    """
    Render a Response using the first compatible registered renderer.
    """
    renderer =  RendererRegistry.resolve(request)

    return renderer.render(response)
