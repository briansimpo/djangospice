from functools import update_wrapper
from inspect import Parameter, signature
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
        from django.http import HttpResponseNotAllowed

        if request.method.upper() not in self.methods:
            return HttpResponseNotAllowed(self.methods)

        parameters = signature(self.func).parameters

        accepts_request = (
            "request" in parameters
            or any(
                parameter.kind == Parameter.VAR_POSITIONAL
                for parameter in parameters.values()
            )
        )

        if accepts_request:
            return self.func(widget, request, *args, **kwargs)

        return self.func(widget, *args, **kwargs)