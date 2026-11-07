from typing import Callable

from .executable import ClassMethod


def action(method: str = "GET", **attributes):
    """Declare an executable action using one HTTP method."""

    def decorator(func: Callable):
        return ClassMethod(func, method=method, **attributes)

    return decorator


def get(func=None, **attributes):
    decorator = action("GET", **attributes)
    return decorator(func) if func else decorator


def post(func=None, **attributes):
    decorator = action("POST", **attributes)
    return decorator(func) if func else decorator


def put(func=None, **attributes):
    decorator = action("PUT", **attributes)
    return decorator(func) if func else decorator


def patch(func=None, **attributes):
    decorator = action("PATCH", **attributes)
    return decorator(func) if func else decorator


def delete(func=None, **attributes):
    decorator = action("DELETE", **attributes)
    return decorator(func) if func else decorator