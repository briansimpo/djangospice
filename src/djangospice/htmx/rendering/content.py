
from __future__ import annotations

from django.http import HttpRequest
from django.template.loader import render_to_string

from djangospice.htmx.response import Response


class ContentRenderer:
    """Render a Response's template or return its existing content."""

    def render(
        self,
        response: Response,
        *,
        request: HttpRequest | None = None,
    ) -> str:
        # Content has already been rendered.
        if response.content is not None:
            return response.content

        # No template and no pre-rendered content.
        if not response.template:
            return ""

        # Render the response template.
        return render_to_string(
            response.template,
            response.payload,
            request=request,
        )
