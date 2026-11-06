from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Any, ClassVar, Callable
from urllib.parse import urlencode
from functools import update_wrapper
from inspect import Parameter, signature
from slugify import slugify

from django.apps import apps
from django.core.exceptions import AppRegistryNotReady
from django.utils.text import camel_case_to_spaces
from djangospice.htmx.querystate import QueryState
from .formatting import snake_case



@dataclass(frozen=True, slots=True)
class ClassIdentity:
    """
    Canonical identity of a registered class.
    """

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

    def to_string(self):
        return str(self)

    @classmethod
    def build(cls, app_name: str, class_name: str) -> "ClassIdentity":
        """
        Build an identity from an application and class/model name.

        Exactly one of class_name or model_name must be provided.
        """
        return cls(
            app_name=app_name, 
            class_name=class_name
         )

    @classmethod
    def from_object(cls, obj: object) -> "ClassIdentity":
        return cls.build(
            app_name=obj.app_name,
            class_name=obj.class_name,
        )

    @classmethod
    def from_class(cls, klass: type) -> "ClassIdentity":
        return cls.from_object(klass)

    @classmethod
    def from_model(cls, model: type) -> "ClassIdentity":
        meta = model._meta

        return cls.build(
            app_name=meta.app_label,
            class_name=meta.model_name,
        )



class Object(ABC):
    """
    Base class for immutable value objects.
    """


class ClassMethod:
    """A Class action bound to one or more HTTP methods."""

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


class Executable:
    suffix: ClassVar[str | None] = None
    app_name: ClassVar[str | None] = None
    class_name: ClassVar[str | None] = None
    title: ClassVar[str | None] = None
   
    
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._configure_identity()

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
        """
        Return the class name without the suffix.
        """
        class_name = str(cls.__name__)

        if cls.suffix is not None:
            if class_name.lower().endswith(cls.suffix.lower()):
                return class_name[: -len(cls.suffix)]

        return class_name

    @classmethod
    def _resolve_class_name(cls) -> str:
        """
        Resolve the canonical identifier as a snake_case slug.
        """
        name = cls._identity_class_name()
        name = snake_case(name)
        return slugify(name, separator="_")

    @classmethod
    def _resolve_app_name(cls, module_path: str) -> str:
        """
        Resolve the Django application label from the module path.

        The longest matching application path is preferred.
        """
        try:
            matches = [
                app_config
                for app_config in apps.get_app_configs()
                if (
                    module_path == app_config.name
                    or module_path.startswith(
                        f"{app_config.name}.",
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
        """
        Resolve the human-readable widget title.

        """
        return camel_case_to_spaces(
            cls._identity_class_name()
        ).title()

    @classmethod
    def get_methods(cls) -> dict[str, ClassMethod]:
        """
        Discover methods declared on this class and its parents.

        Child classes override inherited methods with the same name.
        """
        methods: dict[str, ClassMethod] = {}

        for base in reversed(cls.__mro__):
            for name, value in base.__dict__.items():
                if isinstance(value, ClassMethod):
                    methods[name] = value

        return methods

    def get_method(self, name: str) -> ClassMethod:
        """
        Resolve a registered widget method.
        """
        try:
            return self.get_methods()[name]
        except KeyError:
            raise AttributeError(
                f"Class method '{name}' is not registered."
            ) from None

    def check_method(self, name):
        if name not in self.get_methods():
            raise AttributeError(
                f"Class method '{name}' is not registered."
            )
    
    def get_method_url(self, name: str) -> str:
        """
        Build the URL for a registered widget method.
        """
        self.check_method(name)

        return self.build_url(action=name)
        
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

    @property
    def url(self) -> str:
        url =  self.get_dispatch_url()
        params = {
            key: value
            for key, value in self.kwargs.items()
            if key not in {"id", "app_name", "class_name"}
        }

        if params:
            return f"{url}?{urlencode(params)}"

        return url

    @property
    def base_url(self) -> str:
        return self.url.split("?", 1)[0]

    @property
    def query_state(self) -> QueryState:
        if self.request is None:
            return QueryState()

        return QueryState.from_querydict(
            self.request.GET,
        )

    def get_dispatch_url(self):
        raise NotImplementedError
    
    def build_url(self, *, state: QueryState | None = None, **params: Any) -> str:
        state = state or self.query_state

        for name, value in params.items():
            state = state.set(name, value)

        query = state.encode()

        if query:
            return f"{self.base_url}?{query}"

        return self.base_url

    def get_method_url(self, name: str) -> str:
        """
        Build the URL for a registered widget method.
        """
        self.check_method(name)

        return self.build_url(action=name)





