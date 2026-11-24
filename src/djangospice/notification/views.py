from typing import ClassVar

from django.http import Http404, HttpRequest

from djangospice.exec.dispatchers import (
    Dispatcher,
    MethodDispatcher,
    UnknownDispatcher,
)
from djangospice.exec.views import ExecutableView


class NotificationView(ExecutableView):
    """
    Resolves, initializes, authorizes, and dispatches notifications.
    """

    dispatchers: ClassVar[tuple[type[Dispatcher], ...]] = (
        MethodDispatcher,
        UnknownDispatcher,
    )

    def get_model(self, request: HttpRequest):
        notification_id = (
            request.POST.get("notification_id")
            or request.GET.get("notification_id")
        )

        if not notification_id:
            raise Http404("Notification not found.")

        try:
            return request.user.notifications.get(pk=notification_id)
        except request.user.notifications.model.DoesNotExist:
            raise Http404("Notification not found.") from None

    def prepare_instance(self, instance, request: HttpRequest, action: str | None = None, **kwargs) -> None:
        model = self.get_model(request)
        instance.set_property("action", action)
        instance.set_property("notification", model)