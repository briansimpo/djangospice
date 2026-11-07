from __future__ import annotations

from typing import ClassVar

from django.http import HttpRequest

from djangospice.htmx.response import Response

from .dispatchers import (
    BaseDispatcher,
    MethodDispatcher,
    UnknownActionDispatcher,
)
from .base import Notification


class NotificationExecutor:
    """
    Orchestrates notification initialization, authorization,
    and request dispatching.
    """

    dispatchers: ClassVar[tuple[type[BaseDispatcher], ...]] = (
        MethodDispatcher,
        UnknownActionDispatcher,
    )

    def __init__(self, notification: Notification, request: HttpRequest) -> None:
        self.notification = notification
        self.request = request

    def execute(self) -> Response:
        return self.dispatch()

    def dispatch(self) -> Response:
        for dispatcher_cls in self.dispatchers:
            dispatcher = dispatcher_cls(
                self.notification,
                self.request,
            )

            if dispatcher.can_dispatch():
                return dispatcher.dispatch()

        raise Exception(
            "No valid dispatcher found for this request."
        )