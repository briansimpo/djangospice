from __future__ import annotations

from typing import Any, ClassVar
from slugify import slugify
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

from django.apps import apps
from django.core.exceptions import AppRegistryNotReady, PermissionDenied
from django.utils.text import camel_case_to_spaces

from djangospice.core.formatting import snake_case
from djangospice.htmx.querystate import QueryState
from .action import Action
from .identity import ClassIdentity
from .method import Method


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

    enabled: ClassVar[bool] = True
    login_required: ClassVar[bool] = False
    staff_required: ClassVar[bool] = False
    permissions: ClassVar[tuple[str, ...]] = ()

    def __init__(self, **kwargs: Any) -> None:
        self.request =  kwargs.get("request", None)
        self.user = getattr(self.request, "user", None)
        self.kwargs = kwargs

        super().__init__()


    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._configure_identity()

    # --------------------------------------------------------
    # Lifecycle
    # --------------------------------------------------------

    def initialize(self) -> None:
        """Initialize the component."""

    def configure(self) -> None:
        """Configure component attributes and interactions."""


    # ------------------------------------------------------------------
    # Bindings
    # ------------------------------------------------------------------

    def set_request(self, request) -> None:
        self.request = request
        self.set_user(getattr(request, "user", None))

    def set_user(self, user) -> None:
        self.user = user

    def set_property(self, name: str, value: Any) -> None:
        setattr(self, name, value)


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

    def visible(self) -> bool:
        if not self.enabled:
            return False
        return True
    

    def authorize(self) -> None:

        if self.login_required and not self.user.is_authenticated:
            raise PermissionDenied

        if self.staff_required and not self.user.is_staff:
            raise PermissionDenied

        if self.permissions and not self.user.has_perms(self.permissions):
            raise PermissionDenied

    # -------------------------------------------------------------
    # Method discovery
    # -------------------------------------------------------------

    @classmethod
    def get_methods(cls) -> dict[str, Method]:
        """Discover executable methods across the class hierarchy."""

        methods: dict[str, Method] = {}

        for base in reversed(cls.__mro__):
            for name, value in base.__dict__.items():
                if isinstance(value, Method):
                    methods[name] = value
                else:
                    methods.pop(name, None)

        return methods

    def get_method(self, name: str) -> Method:
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
            path = f"{path.rstrip('/')}/{action}/"

        parts = urlsplit(path)

        # Merge any existing query parameters.
        query_params = dict(parse_qsl(parts.query, keep_blank_values=True))

        # QueryState parameters take precedence.
        query_params.update(state.to_dict())

        query = urlencode(query_params, doseq=True)

        return urlunsplit((
            parts.scheme,
            parts.netloc,
            parts.path,
            query,
            parts.fragment,
        ))
    
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