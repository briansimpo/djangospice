from __future__ import annotations

from typing import ClassVar

from django.http import HttpRequest

from djangospice.htmx.response import Response

from .dispatchers import (
    ActionDispatcher,
    BaseDispatcher,
    HttpDispatcher,
    MethodDispatcher,
    UnknownActionDispatcher,
)
from .exceptions import DispatcherNotFound
from .widget import Widget


class WidgetExecutor:
    """
    Orchestrates widget initialization, authorization,
    and request dispatching.
    """

    dispatchers: ClassVar[tuple[type[BaseDispatcher], ...]] = (
        ActionDispatcher,
        MethodDispatcher,
        UnknownActionDispatcher,
        HttpDispatcher,
    )

    def __init__(self, widget: Widget, request: HttpRequest) -> None:
        self.widget = widget
        self.request = request

    def execute(self) -> Response:
        self.widget.request = self.request
        self.widget.user = getattr(self.request, "user", None)

        self.widget.initialize()
        self.widget.configure()
        self.widget.authorize()

        return self.dispatch()

    def dispatch(self) -> Response:
        for dispatcher_cls in self.dispatchers:
            dispatcher = dispatcher_cls(
                self.widget,
                self.request,
            )

            if dispatcher.can_dispatch():
                return dispatcher.dispatch()

        raise DispatcherNotFound(
            "No valid dispatcher found for this request."
        )