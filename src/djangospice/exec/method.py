from __future__ import annotations

from typing import Any, Callable
from functools import update_wrapper
from inspect import Parameter, signature

from .conf import ActionStyle, ACTION_STYLES, HTTP_METHODS
from .action import Action


class Metadata:
    """
    Metadata attached to an executable method.

    Common presentation attributes are explicitly defined.
    Additional attributes are supported through **attributes.
    """

    __slots__ = (
        "label",
        "icon",
        "style",
        "attributes",
    )

    def __init__(self, *, label: str | None = None, icon: str | None = None, style: ActionStyle = "primary", **attributes: Any) -> None:
        if style not in ACTION_STYLES:
            raise ValueError(f"Invalid action style: {style}")

        self.label = label
        self.icon = icon
        self.style = style
        self.attributes = attributes

    def get(self, name: str, default: Any = None) -> Any:
        if name in {"label", "icon", "style"}:
            return getattr(self, name)

        return self.attributes.get(name, default)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "icon": self.icon,
            "style": self.style,
            **self.attributes,
        }

    def __getattr__(self, name: str) -> Any:
        try:
            return self.attributes[name]
        except KeyError:
            raise AttributeError(name) from None

     
class Method:
    """A class method bound to one HTTP method."""

    def __init__(self, func: Callable | None = None, *, method: str = "GET", **attributes: Any) -> None:
        self.func = None
        self.name: str | None = None
        self.method = method.upper()
        self.metadata = Metadata(**attributes)

        if self.method not in HTTP_METHODS:
            raise ValueError(f"Unsupported HTTP method: {self.method}")

        if func is not None:
            self._set_function(func)

    def _set_function(self, func: Callable) -> None:
        if not callable(func):
            raise TypeError("Method requires a callable.")

        self.func = func
        update_wrapper(self, func)

    def __call__(self, func: Callable) -> Method:
        self._set_function(func)
        return self

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        return instance.get_method_url(self.name)

    def execute(self, executable, request, *args: Any, **kwargs: Any):
        from django.http import HttpResponseNotAllowed

        if request.method.upper() != self.method:
            return HttpResponseNotAllowed([self.method])

        if self.func is None:
            raise RuntimeError(f"Method '{self.name}' has no function.")

        parameters = list(signature(self.func).parameters.values())

        request_parameter = next(
            (
                parameter
                for parameter in parameters
                if parameter.name == "request"
            ),
            None,
        )

        if request_parameter is not None:
            if request_parameter.kind == Parameter.POSITIONAL_ONLY:
                return self.func(
                    executable, request, *args, **kwargs
                )

            if parameters.index(request_parameter) == 1:
                return self.func(executable, request, *args, **kwargs)

            return self.func(executable, *args, request=request, **kwargs)

        return self.func(executable, *args, **kwargs)

    def get_metadata(self) -> dict[str, Any]:
        return self.metadata.to_dict()

    def to_action(self, executable) -> Action:
        return Action(
            name=self.name,
            url=executable.get_method_url(self.name),
            label=self.metadata.label,
            icon=self.metadata.icon,
            method=self.method.lower(),
            style=self.metadata.style,
            attributes=self.metadata.attributes,
        )
