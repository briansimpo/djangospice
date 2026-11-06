

from typing import Callable, Iterable

from djangospice.core.object import ClassMethod


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
        return ClassMethod(fn, methods=methods)

    if func is None:
        return decorator

    return decorator(func)


def method(http_method: str):
    """Create a decorator for a specific HTTP method."""

    def decorator(func):
        return ClassMethod(func, methods=(http_method.upper(),))

    return decorator


def get(func):
    return ClassMethod(func, methods=("GET",))


def post(func):
    return ClassMethod(func, methods=("POST",))


def put(func):
    return ClassMethod(func, methods=("PUT",))


def patch(func):
    return ClassMethod(func, methods=("PATCH",))


def delete(func):
    return ClassMethod(func, methods=("DELETE",))

