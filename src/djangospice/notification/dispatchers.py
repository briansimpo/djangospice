from __future__ import annotations

from abc import ABC, abstractmethod

from django.http import HttpRequest
from djangospice.htmx.response import Response

from .base import Notification


class BaseDispatcher(ABC):
    """Abstract base class for notification dispatchers."""

    def __init__(self, notification: Notification, request: HttpRequest) -> None:
        self.notification = notification
        self.request = request

    @abstractmethod
    def can_dispatch(self) -> bool:
        ...

    @abstractmethod
    def dispatch(self) -> Response:
        ...


class MethodDispatcher(BaseDispatcher):
    """Dispatches registered notification methods through the action parameter."""

    parameter = "action"

    def can_dispatch(self):
        name = self.request.GET.get(self.parameter)

        return bool(
            name and name in self.notification.get_methods()
        )

    def dispatch(self):
        name = self.request.GET.get(self.parameter)

        methods = self.notification.get_methods()
        method = methods.get(name)

        if method is None:
            from django.http import HttpResponseNotFound
            return HttpResponseNotFound("Notification method not found.")

        return method.execute(
            self.notification,
            self.request,
        )


class UnknownActionDispatcher(BaseDispatcher):
    """Rejects unregistered notification actions."""

    parameter = "action"

    def can_dispatch(self) -> bool:
        name = self.request.GET.get(self.parameter)

        return bool(
            name and name in self.notification.get_methods()
        )
        

    def dispatch(self) -> Response:
        from django.http import HttpResponseNotFound

        return HttpResponseNotFound(
            "Notification action not found."
        )

