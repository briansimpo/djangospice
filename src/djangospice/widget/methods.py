
from functools import update_wrapper
from typing import Callable


class Method:
    """A widget action bound to one or more HTTP methods."""

    def __init__(
        self,
        func: Callable | None = None,
        *,
        methods: tuple[str, ...] | list[str] | None = None,
    ):
        self.func = func
        self.methods = tuple(
            method.upper()
            for method in (methods or ("GET",))
        )

        if func is not None:
            update_wrapper(self, func)

    def __call__(self, func: Callable):
        self.func = func
        update_wrapper(self, func)
        return self

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        return instance.get_method_url(self.name)

    def execute(self, widget, request, *args, **kwargs):
        if request.method.upper() not in self.methods:
            from django.http import HttpResponseNotAllowed

            return HttpResponseNotAllowed(self.methods)

        return self.func(widget, request, *args, **kwargs)

