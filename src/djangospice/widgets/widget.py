from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar
from urllib.parse import urlencode

from django.urls import reverse

from djangospice.core.payload import Payload
from djangospice.html.component import HTMLComponent
from djangospice.response.response import Response
from djangospice.widgets.interaction import Interaction
from djangospice.widgets.navigation import Navigation
from djangospice.widgets.querystate import QueryState

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
    from django.db.models import Model, QuerySet
    from django.http import HttpRequest


    from .exceptions import WidgetNotVisible
    from .actions import ActionCollection
    from .metaclass import WidgetMetaclass
    from .options import WidgetOptions
    


class Widget(HTMLComponent, metaclass=WidgetMetaclass):
    """
    Base widget implementation.

    Provides the common widget lifecycle and behavior:

    - Declarative metadata
    - Authorization and visibility
    - Request/data handling
    - Object and queryset resolution
    - HTMX configuration
    - HTTP method dispatch
    - Response rendering
    - Cache configuration
    """

    namespace: ClassVar[str] = "djangospice_widget"

    _meta: ClassVar[WidgetOptions]
    actions: ClassVar[ActionCollection]

    request: HttpRequest | None
    kwargs: dict[str, Any]

    empty_message: ClassVar[str] = "No records found."

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    def __init__(self, request: HttpRequest | None = None, **kwargs: Any ) -> None:
        super().__init__(kwargs=kwargs)
        self.request = request
        self.template_name = self._meta.template_name or self.template_name
        self.initialize()
        self.configure()

    def initialize(self) -> None:
        """
        Hook called immediately after widget construction.

        Override this for initialization that should happen before
        configuration.
        """
        pass

    def configure(self) -> None:
        """
        Hook for configuring widget state.

        Override this in concrete widgets.
        """
        pass

    # -------------------------------------------------------------------------
    # Request / User
    # -------------------------------------------------------------------------

    @property
    def user(self) -> AbstractBaseUser | AnonymousUser | None:
        return getattr(self.request, "user", None)

    @property
    def request_data(self) -> Any:
        """
        Return the request data source appropriate for the HTTP method.

        POST-like methods use POST data; all other methods use GET data.
        """
        if self.request is None:
            return None

        if self.request.method in {"POST", "PUT", "PATCH"}:
            return self.request.POST

        return self.request.GET


    @property
    def navigation(self) -> Navigation:
        return Navigation(self)
    
    @property
    def query_state(self) -> QueryState:
        if self.request is None:
            return QueryState()

        return QueryState.from_querydict(
            self.request.GET
        )

    @property
    def base_url(self) -> str:
        return self.endpoint.split("?", 1)[0]
  
    def url(self, *, state: QueryState | None = None, **params: Any) -> str:
        state = state or self.query_state

        for name, value in params.items():
            state = state.set(name, value)

        query = state.encode()

        return (
            self.base_url
            if not query
            else f"{self.base_url}?{query}"
        )

    def request_value(self, name: str) -> Any:
        """Return a single request parameter."""
        data = self.request_data
        return data.get(name) if data is not None else None

    def request_values(self, name: str) -> list[Any]:
        """Return all values for a request parameter."""
        data = self.request_data
        return data.getlist(name) if data is not None else []

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        context.update(
            widget=self,
            request=self.request,
        )
        return context

    def response(self) -> Response:
        return Response.make(
            self.template_name,
            **self.get_context(),
        )

    def interaction(self, url: str, *, method: str = "GET", target: str | None = None, swap: str = "outerHTML", push_url: bool = True) -> Interaction:

        htmx = (
            self.htmx.request(
                method=method,
                url=url,
            ).target_to(
                target or "this"
            ).swap_to(swap)
        )

        if push_url:
            htmx = htmx.push_url(url)

        return Interaction(
            url=url,
            htmx=htmx,
        )

        # -------------------------------------------------------------------------
        # Metadata
        # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._meta.name

    @property
    def app_label(self) -> str:
        return self._meta.app_label

    @property
    def title(self) -> str:
        return self._meta.title

    @property
    def description(self) -> str:
        return self._meta.description

    @property
    def group(self) -> str | None:
        return self._meta.group

    @property
    def enabled(self) -> bool:
        return self._meta.enabled

    @property
    def permission(self) -> str | None:
        return self._meta.permission

    @property
    def priority(self) -> int:
        return self._meta.priority

    @property
    def lazy(self) -> bool:
        return self._meta.lazy

    @property
    def refreshable(self) -> bool:
        return self._meta.refreshable

    @property
    def refresh_interval(self) -> int | None:
        return self._meta.refresh_interval

    @property
    def cache_timeout(self) -> int | None:
        return self._meta.cache_timeout

    @property
    def cache_enabled(self) -> bool:
        return self.cache_timeout is not None

    @property
    def widget_key(self) -> str:
        return (
            f"{self.app_label}.{self.name}"
            if self.app_label
            else self.name
        )

    # -------------------------------------------------------------------------
    # Visibility / Authorization
    # -------------------------------------------------------------------------

    def authorize(self) -> None:
        """Raise WidgetNotVisible when the widget is not accessible."""
        if not self.visible():
            raise WidgetNotVisible

    def visible(self) -> bool:
        """
        Return whether the widget is enabled and accessible to the
        current user.
        """
        if not self.enabled:
            return False

        if self.permission and not self._has_permission():
            return False

        return self.is_visible()

    def _has_permission(self) -> bool:
        """Check the configured permission against the current user."""
        user = self.user

        return bool(
            user
            and user.is_authenticated
            and user.has_perm(self.permission)
        )

    def is_visible(self) -> bool:
        """
        Application-specific visibility hook.

        Override this when visibility depends on business rules.
        """
        return True

    # -------------------------------------------------------------------------
    # HTMX
    # -------------------------------------------------------------------------

    @property
    def endpoint(self) -> str:
        """Return the URL used to fetch this widget."""
        url = reverse(
            self.namespace,
            kwargs={
                "app_label": self.app_label,
                "name": self.name,
            },
        )

        params = {
            key: value
            for key, value in self.kwargs.items()
            if key != "id"
        }

        if not params:
            return url

        return f"{url}?{urlencode(params)}"

    @property
    def is_lazy_fetch(self) -> bool:
        """
        Return whether this request is an HTMX request specifically
        targeting this widget's endpoint.
        """
        request = self.request

        if not request:
            return False

        if request.headers.get("HX-Request") != "true":
            return False

        match = request.resolver_match

        return bool(
            match
            and match.view_name == self.namespace
            and match.kwargs.get("app_label") == self.app_label
            and match.kwargs.get("name") == self.name
        )

    def configure_htmx(self) -> None:
        """Configure lazy loading and automatic refresh behavior."""
        if self.lazy:
            (
                self.htmx
                .get(self.endpoint)
                .trigger_on("load")
                .target_to("this")
                .swap_to("outerHTML")
            )

        if self.refreshable and self.refresh_interval:
            trigger = getattr(self.htmx, "trigger", None) or "load"

            (
                self.htmx
                .trigger_on(
                    f"{trigger}, every {self.refresh_interval}s"
                )
                .target_to("this")
            )

    # -------------------------------------------------------------------------
    # Data / QuerySets
    # -------------------------------------------------------------------------

    def get_queryset(self) -> QuerySet[Model]:
        """
        Return the widget's base queryset.

        Concrete widgets can override this to add filtering, annotations,
        select_related(), prefetch_related(), etc.
        """
        model = self._meta.model

        if model is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define 'model' in Meta "
                "or override get_queryset()."
            )

        return model._default_manager.all()

    def get_object(self) -> Model | None:
        """Resolve a single object from the request."""
        pk = self.request_value(self._meta.object_parameter)

        if not pk:
            return None

        return self.get_queryset().filter(pk=pk).first()

    def get_objects(self) -> tuple[Model, ...]:
        """
        Resolve multiple objects from the request.

        If no multiple-object parameter is supplied, fall back to the
        single-object parameter.
        """
        ids = self.request_values(self._meta.objects_parameter)

        if not ids:
            obj = self.get_object()
            return (obj,) if obj else ()

        return tuple(
            self.get_queryset().filter(pk__in=ids)
        )

    def get_data(self) -> Payload:
        """Return request parameters as a Payload."""
        data = self.request_data

        if data is None:
            return Payload()

        return Payload.from_dict(data.dict())

    # -------------------------------------------------------------------------
    # HTTP
    # -------------------------------------------------------------------------

    def get(self) -> Response:
        return self.response()

    def post(self) -> Response:
        return self.method_not_allowed()

    def put(self) -> Response:
        return self.method_not_allowed()

    def patch(self) -> Response:
        return self.method_not_allowed()

    def delete(self) -> Response:
        return self.method_not_allowed()

    def method_not_allowed(self) -> Response:
        return Response.empty(status=405)

    # -------------------------------------------------------------------------
    # Cache
    # -------------------------------------------------------------------------

    def should_cache(self) -> bool:
        """Return whether this widget should use caching."""
        return self.cache_enabled

    def cache_key(self) -> str:
        """Build a cache key for the current widget state."""
        return ":".join(
            (
                self.namespace,
                self.widget_key,
                self.cache_identifier(),
                self.generate_state_hash(),
            )
        )

    def cache_identifier(self) -> str:
        """
        Return the user-specific portion of the cache key.

        Override this when cache identity needs to include additional
        information such as tenant, organization, or session.
        """
        user = self.user

        if user and user.is_authenticated:
            return str(user.pk)

        return "anonymous"

    def generate_state_hash(self) -> str:
        """
        Return a value representing the state that affects rendered output.

        Override this when the widget's output depends on request parameters,
        filters, selected objects, etc.
        """
        return "default"
