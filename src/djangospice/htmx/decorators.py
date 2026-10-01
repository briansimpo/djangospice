from __future__ import annotations

from functools import wraps
from typing import Callable, ParamSpec, TypeVar
from django.http import Http404

from .request import is_htmx

P = ParamSpec("P"); R = TypeVar("R")

def htmx_required(view: Callable[P, R]) -> Callable[P, R]:
    """Reject non-HTMX requests with HTTP 404."""
    @wraps(view)
    def wrapped(request, *args: P.args, **kwargs: P.kwargs):
        if not is_htmx(request): raise Http404
        return view(request, *args, **kwargs)
    return wrapped
