from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from .request import attach_htmx_info
from .response import Response
from .shortcuts import render_response


class HTMXMiddleware(MiddlewareMixin):
    """
    Integrates HTMX request metadata and Djangospice Response objects
    into Django's request/response lifecycle.
    """

    def process_request(self, request: HttpRequest) -> None:
        attach_htmx_info(request)

    def process_response(self,request: HttpRequest, response: HttpResponse | Response) -> HttpResponse:
        if isinstance(response, Response):
            return render_response(request, response)

        return response