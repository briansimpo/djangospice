from __future__ import annotations

from typing import ClassVar

from django.http import HttpRequest

from djangospice.htmx.response import Response
from djangospice.exec.dispatchers import Dispatcher, MethodDispatcher, UnknownDispatcher
from .dispatchers import ActionDispatcher, HttpDispatcher
from .widget import Widget


class WidgetExecutor:
    """
    Orchestrates widget initialization, authorization,
    and request dispatching.
    """

    dispatchers: ClassVar[tuple[type[Dispatcher], ...]] = (
        ActionDispatcher,
        MethodDispatcher,
        UnknownDispatcher,
        HttpDispatcher,
    )

    def __init__(self, widget: Widget, request: HttpRequest,*, action: str | None = None) -> None:
        self.widget = widget
        self.request = request
        self.action = action

    def execute(self) -> Response:
        self.widget.set_request(self.request)
        
        self.widget.initialize()
        self.widget.configure()
        self.widget.authorize()

        return self.dispatch()

    def dispatch(self) -> Response:
        for dispatcher_cls in self.dispatchers:
            dispatcher = dispatcher_cls(
                self.widget,
                self.request,
                action=self.action,
            )

            if dispatcher.can_dispatch():
                return dispatcher.dispatch()

        raise Exception("No valid dispatcher found for this request.")