from __future__ import annotations

from django.http import HttpResponse
from django.http import HttpRequest

from djangospice.htmx.response import Response


class DocumentRenderer:
    """
    Materializes Response document content into HttpResponse.
    """

    def render(
        self,
        response: Response,
        *,
        request: HttpRequest | None = None,
    ) -> HttpResponse:
        document = response._document

        if document is None:
            raise ValueError(
                "Response has no document."
            )

        http_response = HttpResponse(
            content=document.content,
            status=response.status,
            content_type=document.content_type,
        )

        if document.filename:
            http_response.headers[
                "Content-Disposition"
            ] = (
                f"{document.disposition}; "
                f'filename="{document.filename}"'
            )

        return http_response