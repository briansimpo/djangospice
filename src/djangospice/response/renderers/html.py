from __future__ import annotations

from typing import Any

from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string

from djangospice.response.response import Response

from .base import BaseRenderer


class HTMLRenderer(BaseRenderer[HttpResponse, str]):
    """
    Renders a transport-agnostic Response as a standard HTML HttpResponse.

    This serves as the default fallback renderer within the djangospice pipeline.
    """

    name: str = "html"
    priority: int = 100

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def supports(self, request: HttpRequest | None) -> bool:
        """
        HTML is the catch-all default renderer and always returns True.
        """
        return True

    # ------------------------------------------------------------------
    # Data Extraction Helpers
    # ------------------------------------------------------------------

    def get_template(self, response: Response) -> str:
        """
        Extract and validate the template path from the response object.

        Raises:
            ValueError: If the response does not specify a template path.
        """
        if not response.template:
            raise ValueError(
                f"{self.__class__.__name__} requires a valid template path."
            )

        return response.template

    def get_context(self, response: Response) -> dict[str, Any]:
        """
        Build the template rendering context dictionary from the response payload.
        """
        return response.payload.to_dict()

    # ------------------------------------------------------------------
    # Pipeline Content Delivery
    # ------------------------------------------------------------------

    def build_content(self, response: Response) -> str:
        """
        Render the designated response template into a flat HTML string.
        """
        # Guard against AttributeError: Response utilizes slots=True and does
        # not natively include a 'request' field. We use getattr safely here.
        request = getattr(response, "request", None)

        return render_to_string(
            template_name=self.get_template(response),
            context=self.get_context(response),
            request=request,
        )

    # ------------------------------------------------------------------
    # Response Compilation
    # ------------------------------------------------------------------

    def build_response(self, response: Response, content: str) -> HttpResponse:
        """
        Wrap the rendered HTML string inside a native Django HttpResponse.
        """
        return HttpResponse(
            content=content,
            status=response.status,
            content_type="text/html",
        )