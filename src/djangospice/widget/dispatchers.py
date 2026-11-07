from __future__ import annotations

from abc import ABC, abstractmethod

from django.http import HttpRequest
from djangospice.htmx.response import Response

from .actions import ActionContext
from .widget import Widget


class BaseDispatcher(ABC):
    """Abstract base class for widget dispatchers."""

    def __init__(self, widget: Widget, request: HttpRequest) -> None:
        self.widget = widget
        self.request = request

    @abstractmethod
    def can_dispatch(self) -> bool:
        ...

    @abstractmethod
    def dispatch(self) -> Response:
        ...


class ActionDispatcher(BaseDispatcher):
    """Dispatches custom actions declared on the widget."""
   
    parameter = "action"

    def can_dispatch(self):
        name = self.request.GET.get(self.parameter)

        return bool(
            name and self.widget.get_action_collection().get(name)
        )

    def dispatch(self):
        name = self.request.GET.get(self.parameter)

        actions = self.widget.get_action_collection()
        action = actions.require(name)

        context = ActionContext(
            widget=self.widget,
            request=self.request,
            object=self.widget.get_object(),
            objects=self.widget.get_objects(),
            data=self.widget.get_data(),
        )

        return action.dispatch(context)


class MethodDispatcher(BaseDispatcher):
    """Dispatches registered widget methods through the action parameter."""

    parameter = "action"

    def can_dispatch(self):
        name = self.request.GET.get(self.parameter)

        return bool(
            name and name in self.widget.get_methods()
        )

    def dispatch(self):
        name = self.request.GET.get(self.parameter)

        methods = self.widget.get_methods()
        method = methods.get(name)

        if method is None:
            from django.http import HttpResponseNotFound
            return HttpResponseNotFound("Widget method not found.")

        return method.execute(
            self.widget,
            self.request,
        )


class UnknownActionDispatcher(BaseDispatcher):
    """Rejects unregistered widget actions."""

    parameter = "action"

    def can_dispatch(self) -> bool:
        name = self.request.GET.get(self.parameter)

        return bool(
            name and name in self.widget.get_methods()
        )
        

    def dispatch(self) -> Response:
        from django.http import HttpResponseNotFound

        return HttpResponseNotFound(
            "Widget action not found."
        )


class HttpDispatcher(BaseDispatcher):
    """Dispatches standard HTTP methods to widget handlers."""

    def can_dispatch(self) -> bool:
        return True

    def dispatch(self) -> Response:
        handler = getattr(
            self.widget,
            self.request.method.lower(),
            None,
        )

        if not callable(handler):
            return self.widget.method_not_allowed()

        return handler()