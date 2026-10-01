from __future__ import annotations

from dataclasses import dataclass
from django.http import HttpRequest

_TRUE = "true"


@dataclass(frozen=True, slots=True)
class HTMXRequestInfo:
    is_htmx: bool
    boosted: bool = False
    current_url: str | None = None
    history_restore_request: bool = False
    prompt: str | None = None
    target: str | None = None
    trigger: str | None = None
    trigger_name: str | None = None

    @property
    def is_boosted(self) -> bool:
        return self.boosted


def is_htmx(request: HttpRequest) -> bool:
    return request.headers.get("HX-Request") == _TRUE


def make_htmx_request_info(request: HttpRequest) -> HTMXRequestInfo:
    headers = request.headers
    return HTMXRequestInfo(
        is_htmx=headers.get("HX-Request") == _TRUE,
        boosted=headers.get("HX-Boosted") == _TRUE,
        current_url=headers.get("HX-Current-URL"),
        history_restore_request=headers.get("HX-History-Restore-Request") == _TRUE,
        prompt=headers.get("HX-Prompt"),
        target=headers.get("HX-Target"),
        trigger=headers.get("HX-Trigger"),
        trigger_name=headers.get("HX-Trigger-Name"),
    )


def attach_htmx_info(request: HttpRequest) -> HTMXRequestInfo:
    info = make_htmx_request_info(request)
    request.htmx = info
    return info


def get_htmx_info(request: HttpRequest) -> HTMXRequestInfo:
    return getattr(request, "htmx", make_htmx_request_info(request))
