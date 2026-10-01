from __future__ import annotations

from django.http import HttpResponse

from djangospice.htmx.response import Response


class HeaderRenderer:
    """
    Applies ordinary HTTP and HTMX response headers.
    """

    def render(
        self,
        response: Response,
        http_response: HttpResponse,
    ) -> None:
        self.render_http_headers(
            response,
            http_response,
        )

        self.render_htmx_headers(
            response,
            http_response,
        )

    def render_http_headers(
        self,
        response: Response,
        http_response: HttpResponse,
    ) -> None:
        for name, value in response.headers.items():
            http_response.headers[name] = str(value)

    def render_htmx_headers(
        self,
        response: Response,
        http_response: HttpResponse,
    ) -> None:
        if not response.has_htmx:
            return

        for name, value in response._htmx.to_dict().items():
            http_response.headers[name] = value