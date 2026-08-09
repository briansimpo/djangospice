from __future__ import annotations

from django.http import HttpRequest, HttpResponse

from djangospice.response.response import Response

from .base import BaseRenderer


class TextRenderer(BaseRenderer[HttpResponse, str]):
    """
    Renders a Response as plain text.

    This renderer acts as the ultimate fallback when no other
    renderer supports the current request.
    """

    name = "text"

    #: Always evaluated last.
    priority = 999

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def supports(self, request: HttpRequest | None) -> bool:
        """
        Always returns True.

        Since this renderer has the lowest priority, it is selected
        only when no other renderer supports the request.
        """
        return True

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    def build_content(self, response: Response) -> str:
        """
        Build the plain-text representation.
        """

        if response.payload:
            return str(response.payload)

        return ""

    # ------------------------------------------------------------------
    # Response
    # ------------------------------------------------------------------

    def build_response(self, response: Response, content: str) -> HttpResponse:
        """
        Build the plain-text HttpResponse.
        """

        return HttpResponse(
            content=content,
            status=response.status,
            content_type="text/plain; charset=utf-8",
        )