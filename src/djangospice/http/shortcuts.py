from __future__ import annotations

import json
from typing import Any

from djangospice.http.headers import HTMXHeaders

from .response import Response


def response(
    content: str | bytes = b"",
    *,
    status: int = 200,
    content_type: str = "text/html; charset=utf-8",
    template: str | None = None,
    context: dict[str, Any] | None = None,
    htmx: HTMXHeaders | None = None,
) -> Response:
    return Response(
        content, 
        status=status, 
        content_type=content_type, 
        template=template, 
        context=context, 
        htmx=htmx
    )


def redirect_to(to: str,) -> Response:
    return Response.redirect_to(to)


def navigate_to(
    to: str,
    *,
    target: str | None = "spice-app",
    select: str | None = "spice-app",
    swap: str | None = "innerHTML",
    
) -> Response:

    return Response.navigate_to(
        to=to,
        target=target,
        swap=swap,
        select=select
    )