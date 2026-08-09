from __future__ import annotations

from typing import Any

from django.http import HttpRequest, JsonResponse

from djangospice.response.response import Response

from .base import BaseRenderer


class JSONRenderer(BaseRenderer[JsonResponse, dict[str, Any]]):
    """
    Renders a Response as JSON.
    """

    name = "json"

    priority = 50

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def supports(self, request: HttpRequest | None) -> bool:
        """
        Return True when JSON has been requested.
        """

        if request is None:
            return False

        accept = request.headers.get("Accept", "")

        return (
            "application/json" in accept
            or request.content_type == "application/json"
        )

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    def build_content(self, response: Response) -> dict[str, Any]:
        """
        Build the JSON payload.
        """

        return response.payload.to_dict()

    # ------------------------------------------------------------------
    # Response
    # ------------------------------------------------------------------

    def build_response(self, response: Response, content: dict[str, Any]) -> JsonResponse:
        """
        Build the JsonResponse.
        """

        return JsonResponse(
            data=content,
            status=response.status,
        )