from __future__ import annotations

from djangospice.exec.dispatchers import Dispatcher
from djangospice.htmx.response import Response

from .actions import ActionContext
from .widget import Widget


class ActionDispatcher(Dispatcher[Widget]):
    """Dispatches custom actions declared on the executable."""

    def can_dispatch(self) -> bool:
        return bool(
            self.action
            and self.executable.get_action_collection().get(self.action)
        )

    def dispatch(self) -> Response:
        actions = self.executable.get_action_collection()
        action = actions.require(self.action)

        context = ActionContext(
            executable=self.executable,
            request=self.request,
            object=self.executable.get_object(),
            objects=self.executable.get_objects(),
            data=self.executable.get_data(),
        )

        return action.dispatch(context)


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