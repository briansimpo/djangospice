from __future__ import annotations

from djangospice.exec.dispatchers import Dispatcher
from djangospice.htmx.response import Response

from .widget import Widget


class HttpDispatcher(Dispatcher[Widget]):
    """Dispatches standard HTTP methods to executable handlers."""

    def can_dispatch(self) -> bool:
        return self.action is None

    def dispatch(self) -> Response:
        handler = getattr(
            self.executable,
            self.request.method.lower(),
            None,
        )

        if not callable(handler):
            return self.executable.method_not_allowed()

        return handler()