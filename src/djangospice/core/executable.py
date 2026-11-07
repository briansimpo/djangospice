from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Literal, Generic, TypeVar
from copy import deepcopy
from dataclasses import dataclass, field
from functools import update_wrapper
from inspect import Parameter, signature
from slugify import slugify

from django.apps import apps
from django.urls import get_script_prefix
from django.utils.translation import get_language
from django.core.exceptions import AppRegistryNotReady
from django.http import HttpRequest, HttpResponseNotFound
from django.utils.text import camel_case_to_spaces

from djangospice.core.serializable import Serializable
from djangospice.htmx.querystate import QueryState
from djangospice.htmx.response import Response

from .formatting import snake_case


ActionStyle = Literal[
    "primary",
    "secondary",
    "success",
    "warning",
    "danger",
]

ACTION_STYLES = {
    "primary",
    "secondary",
    "success",
    "warning",
    "danger",
}

HTTP_METHODS = {"GET", "POST"}



@dataclass(frozen=True, slots=True)
class ClassIdentity:
    """Canonical identity of a registered class."""

    app_name: str
    class_name: str

    def __post_init__(self) -> None:
        app_name = str(self.app_name).strip().casefold()
        class_name = str(self.class_name).strip().casefold()

        if not app_name:
            raise ValueError("app_name cannot be empty.")

        if not class_name:
            raise ValueError("class_name cannot be empty.")

        object.__setattr__(self, "app_name", app_name)
        object.__setattr__(self, "class_name", class_name)

    def __str__(self) -> str:
        return f"{self.app_name}.{self.class_name}"

    def to_string(self) -> str:
        return str(self)

    @classmethod
    def build(
        cls,
        app_name: str,
        class_name: str,
    ) -> ClassIdentity:
        return cls(
            app_name=app_name,
            class_name=class_name,
        )

    @classmethod
    def from_object(cls, obj: object) -> ClassIdentity:
        return cls.build(
            app_name=obj.app_name,
            class_name=obj.class_name,
        )

    @classmethod
    def from_class(cls, klass: type) -> ClassIdentity:
        return cls.from_object(klass)

    @classmethod
    def from_model(cls, model: type) -> ClassIdentity:
        meta = model._meta

        return cls.build(
            app_name=meta.app_label,
            class_name=meta.model_name,
        )


class MethodMetadata:
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


@dataclass(frozen=True, slots=True)
class Action(Serializable):
    """Serializable representation of an executable action."""

    name: str
    url: str
    label: str | None = None
    icon: str | None = None
    method: Literal["get", "post"] = "get"
    style: ActionStyle = "primary"
    status: str = "pending"
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        method = self.method.lower()

        if method not in {"get", "post"}:
            raise ValueError(
                f"Unsupported action method: {method}"
            )

        if self.style not in ACTION_STYLES:
            raise ValueError(
                f"Invalid action style: {self.style}"
            )

        object.__setattr__(self, "method", method)
        object.__setattr__(
            self,
            "attributes",
            deepcopy(self.attributes),
        )

        if self.label is None:
            label = (
                self.name
                .replace("_", " ")
                .replace("-", " ")
                .title()
            )
            object.__setattr__(self, "label", label)


@dataclass(frozen=True, slots=True)
class PostAction(Action):
    method: Literal["post"] = field(
        default="post",
        init=False,
    )


@dataclass(frozen=True, slots=True)
class GetAction(Action):
    method: Literal["get"] = field(
        default="get",
        init=False,
    )


class ClassMethod:
    """A class method bound to one HTTP method."""

    def __init__(self, func: Callable | None = None, *, method: str = "GET", **attributes: Any) -> None:
        self.func = None
        self.name: str | None = None
        self.method = method.upper()
        self.metadata = MethodMetadata(**attributes)

        if self.method not in HTTP_METHODS:
            raise ValueError(f"Unsupported HTTP method: {self.method}")

        if func is not None:
            self._set_function(func)

    def _set_function(self, func: Callable) -> None:
        if not callable(func):
            raise TypeError("ClassMethod requires a callable.")

        self.func = func
        update_wrapper(self, func)

    def __call__(self, func: Callable) -> ClassMethod:
        self._set_function(func)
        return self

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        return instance.get_method_url(self.name)

    def execute(self, executable: Executable, request, *args: Any, **kwargs: Any):
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

    def to_action(self, executable: Executable) -> Action:
        return Action(
            name=self.name,
            url=executable.get_method_url(self.name),
            label=self.metadata.label,
            icon=self.metadata.icon,
            method=self.method.lower(),
            style=self.metadata.style,
            attributes=self.metadata.attributes,
        )


class Executable:
    """
    Mixin providing executable method discovery, identity and URLs.

    Initialization is independent of other classes in the MRO.
    """

    suffix: ClassVar[str | None] = None
    app_name: ClassVar[str | None] = None
    class_name: ClassVar[str | None] = None
    namespace: ClassVar[str | None] = None
    title: ClassVar[str | None] = None

    def __init__(self, *, request=None, **kwargs: Any) -> None:
        self.request = request
        self.user = getattr(request, "user", None)
        self.kwargs = kwargs
        super().__init__()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._configure_identity()

    # -------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------

    @classmethod
    def _configure_identity(cls) -> None:
        if cls.__dict__.get("class_name") is None:
            cls.class_name = cls._resolve_class_name()

        if cls.__dict__.get("app_name") is None:
            cls.app_name = cls._resolve_app_name(cls.__module__)

        if cls.__dict__.get("title") is None:
            cls.title = cls._resolve_title()

    @classmethod
    def _identity_class_name(cls) -> str:
        class_name = cls.__name__

        if (
            cls.suffix is not None
            and class_name.lower().endswith(cls.suffix.lower())
        ):
            return class_name[:-len(cls.suffix)]

        return class_name

    @classmethod
    def _resolve_class_name(cls) -> str:
        name = snake_case(cls._identity_class_name())
        return slugify(name, separator="_")

    @classmethod
    def _resolve_app_name(cls, module_path: str) -> str:
        try:
            matches = [
                app_config
                for app_config in apps.get_app_configs()
                if (
                    module_path == app_config.name
                    or module_path.startswith(
                        f"{app_config.name}."
                    )
                )
            ]

            if matches:
                return max(
                    matches,
                    key=lambda app_config: len(app_config.name),
                ).label

        except AppRegistryNotReady:
            pass

        return module_path.split(".", 1)[0]

    @classmethod
    def _resolve_title(cls) -> str:
        return camel_case_to_spaces(
            cls._identity_class_name()
        ).title()

    @property
    def identity(self) -> ClassIdentity:
        return ClassIdentity.from_object(self)

    @property
    def identifier(self) -> str:
        return str(self.identity)

    @property
    def id(self) -> str:
        if self.suffix is None:
            return self.class_name

        return f"{self.class_name}_{self.suffix.lower()}"

    # -------------------------------------------------------------
    # Method discovery
    # -------------------------------------------------------------

    @classmethod
    def get_methods(cls) -> dict[str, ClassMethod]:
        """Discover executable methods across the class hierarchy."""

        methods: dict[str, ClassMethod] = {}

        for base in reversed(cls.__mro__):
            for name, value in base.__dict__.items():
                if isinstance(value, ClassMethod):
                    methods[name] = value
                else:
                    methods.pop(name, None)

        return methods

    def get_method(self, name: str) -> ClassMethod:
        try:
            return self.get_methods()[name]
        except KeyError:
            raise AttributeError(
                f"Class method '{name}' is not registered."
            ) from None

    def check_method(self, name: str) -> None:
        self.get_method(name)

    # -------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------

    def get_actions(self) -> list[Action]:
        return [
            method.to_action(self)
            for method in self.get_methods().values()
        ]

    # -------------------------------------------------------------
    # URLs
    # -------------------------------------------------------------

    
    @property
    def base_url(self) -> str:
        return self.dispatch_url()


    def build_url(self, *, action: str | None = None, state: QueryState | None = None, **params: Any) -> str:
        state = state or self.query_state

        for name, value in params.items():
            state = state.set(name, value)

        path = self.base_url

        if action:
            path = f"{path}{action}/"

        query = state.encode()
        url = f"{path}?{query}" if query else path

        return url
    
    def get_method_url(self, name: str) -> str:
        self.get_method(name)
        return self.build_url(action=name)

    @property
    def url(self) -> str:
        return self.build_url(**self.kwargs)

    @property
    def query_state(self) -> QueryState:
        if self.request is None:
            return QueryState()

        return QueryState.from_querydict(self.request.GET)

    def dispatch_url(self):
        raise NotImplementedError


ExecutableT = TypeVar("ExecutableT", bound=Executable)


class Dispatcher(ABC, Generic[ExecutableT]):
    """Abstract base class for executable dispatchers."""

    def __init__(self, executable: ExecutableT, request: HttpRequest, *, action: str | None = None) -> None:
        self.executable = executable
        self.request = request
        self.action = action

    @abstractmethod
    def can_dispatch(self) -> bool:
        ...

    @abstractmethod
    def dispatch(self) -> Response:
        ...

class MethodDispatcher(Dispatcher[Executable]):
    """Dispatches registered executable methods."""

    def can_dispatch(self) -> bool:
        return bool(
            self.action
            and self.action in self.executable.get_methods()
        )

    def dispatch(self) -> Response:
        method = self.executable.get_method(self.action)

        return method.execute(
            self.executable,
            self.request,
        )


class UnknownDispatcher(Dispatcher[Executable]):
    """Rejects unregistered widget actions."""

    def can_dispatch(self) -> bool:
        return self.action is not None

    def dispatch(self) -> Response:
        return HttpResponseNotFound(
            f"Widget action '{self.action}' not found."
        )


class DispatcherNotFound(Exception):
    pass
