from __future__ import annotations

from collections.abc import Callable, Iterable

from .methods import Method
from .registry import WidgetRegistry


def widget(widget_class):
    """
    Register a Widget class explicitly.
    """
    WidgetRegistry.register(widget_class)
    return widget_class


def action(func=None, *, methods: Iterable[str] | None = None):
    """
    Register a widget method as an action.

    Defaults to POST.

    Usage:
        @action
        def archive(self, request):
            ...

        @action()
        def archive(self, request):
            ...

        @action(methods=["POST", "DELETE"])
        def archive(self, request):
            ...
    """
    def decorator(fn: Callable):
        return Method(fn, methods=methods)

    if func is None:
        return decorator

    return decorator(func)


def method(http_method: str):
    """Create a decorator for a specific HTTP method."""

    def decorator(func):
        return Method(func, methods=(http_method.upper(),))

    return decorator


def get(func):
    return Method(func, methods=("GET",))


def post(func):
    return Method(func, methods=("POST",))


def put(func):
    return Method(func, methods=("PUT",))


def patch(func):
    return Method(func, methods=("PATCH",))


def delete(func):
    return Method(func, methods=("DELETE",))

