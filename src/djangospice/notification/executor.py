from __future__ import annotations

from typing import ClassVar

from django.http import Http404, HttpRequest

from djangospice.htmx.response import Response
from djangospice.exec.dispatchers import Dispatcher, MethodDispatcher, UnknownDispatcher

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

    def get_notification_model(self):
        notification_id = (
            self.request.POST.get("notification_id")
            or self.request.GET.get("notification_id")
        )

        if not notification_id:
            raise Http404("Notification not found.")

        try:
            return self.request.user.notifications.get(pk=notification_id)
        except self.request.user.notifications.model.DoesNotExist:
            raise Http404("Notification not found.") from None
   
    def execute(self) -> Response:
        notification_model = self.get_notification_model()

        self.notification.set_request(self.request)
        self.notification.set_property("action", self.action)
        self.notification.set_property("notification", notification_model)
        self.notification.authorize()

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

        raise Exception("No valid dispatcher found for this request.")