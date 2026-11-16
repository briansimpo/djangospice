from __future__ import annotations

from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin

from .request import attach_htmx_info


class HTMXMiddleware(MiddlewareMixin):
    """
    Integrates HTMX request metadata and Djangospice Response objects
    into Django's request/response lifecycle.
    """

    def process_request(self, request: HttpRequest) -> None:
        attach_htmx_info(request)
