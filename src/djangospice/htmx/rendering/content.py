from __future__ import annotations

from django.http import HttpRequest
from django.template.loader import render_to_string

from djangospice.htmx.response import Response


class ContentRenderer:
    """
    Renders the primary Response template.
    """

    def render(self, response: Response, *, request: HttpRequest | None = None) -> str:
        if not response.template:
            return ""

        return render_to_string(
            response.template,
            response.payload,
            request=request,
        )