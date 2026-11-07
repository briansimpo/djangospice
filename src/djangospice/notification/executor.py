from __future__ import annotations

from typing import ClassVar

from django.http import HttpRequest

from djangospice.htmx.response import Response
from djangospice.core.executable import Dispatcher, MethodDispatcher, UnknownDispatcher, DispatcherNotFound

from .base import Notification


class NotificationExecutor:
    """
    Orchestrates notification initialization, authorization,
    and request dispatching.
    """

    dispatchers: ClassVar[tuple[type[Dispatcher], ...]] = (
        MethodDispatcher,
        UnknownDispatcher,
    )

    def __init__(self, notification: Notification, request: HttpRequest,*, action: str | None = None) -> None:
           self.notification = notification
           self.request = request
           self.action = action
   
    def execute(self) -> Response:
        self.notification.request = self.request
        self.notification.user = getattr(self.request, "user", None)
        return self.dispatch()

    def dispatch(self) -> Response:
        for dispatcher_cls in self.dispatchers:
            dispatcher = dispatcher_cls(
                self.notification,
                self.request,
                action=self.action,
            )

            if dispatcher.can_dispatch():
                return dispatcher.dispatch()

        raise DispatcherNotFound("No valid dispatcher found for this request.")