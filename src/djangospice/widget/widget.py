
from __future__ import annotations

from typing import Any, ClassVar

from django.db.models import Model, QuerySet

from djangospice.exec.mixin import Executable
from djangospice.htmx.component import Component
from djangospice.htmx.response import Response
from djangospice.utils import safe_reverse

from .apps import namespace


class Widget(Executable, Component):
    """
    Base class for Djangospice UI widgets.

    Widget combines executable behavior with component rendering.

    Responsibilities:
    - action registration and binding
    - request visibility and data resolution
    - model/queryset access
    - HTMX refresh configuration
    - caching
    - HTTP response generation

    Component owns composition, slots, context and rendering.
    Executable owns identity, URL generation and method dispatch.
    """

    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------

    description: ClassVar[str] = ""
    suffix: ClassVar[str] = "Widget"

    priority: ClassVar[int] = 100

    model: ClassVar[type[Model] | None] = None
    object_parameter: ClassVar[str] = "selected_id"
    objects_parameter: ClassVar[str] = "selected_ids"

    namespace: ClassVar[str] = namespace

    lazy: ClassVar[bool] = True

    refreshable: ClassVar[bool] = False
    refresh_interval: ClassVar[int | None] = None

    cache_timeout: ClassVar[int | None] = None

    template_name: ClassVar[str | None] = None

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
   
    
    # ------------------------------------------------------------------
    # Request & visibility
    # ------------------------------------------------------------------

    @property
    def is_lazy_fetch(self) -> bool:
        request = self.request

        if request is None:
            return False

        if request.headers.get("HX-Request") != "true":
            return False

        match = request.resolver_match

        return bool(
            match
            and match.view_name == self.namespace
            and match.kwargs.get("app_name") == self.app_name
            and match.kwargs.get("class_name") == self.class_name
        )

    def get_data(self):
        if self.request is None:
            return None

        if self.request.method in {"POST", "PUT", "PATCH"}:
            return self.request.POST

        return self.request.GET

    def get_value(self, name: str) -> Any:
        data = self.get_data()
        return data.get(name) if data is not None else None

    def get_list(self, name: str) -> list[Any]:
        data = self.get_data()
        return data.getlist(name) if data is not None else []

    # ------------------------------------------------------------------
    # Data resolution
    # ------------------------------------------------------------------

    def get_queryset(self) -> QuerySet[Model]:
        if self.model is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define "
                "'model' or override 'get_queryset()'."
            )

        return self.model._default_manager.all()

    def get_object(self) -> Model | None:
        pk = self.get_value(self.object_parameter)

        if not pk:
            return None

        return self.get_queryset().filter(pk=pk).first()

    def get_objects(self) -> tuple[Model, ...]:
        ids = self.get_list(self.objects_parameter)

        if not ids:
            obj = self.get_object()
            return (obj,) if obj else ()

        return tuple(
            self.get_queryset().filter(pk__in=ids)
        )

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def get_refresh_event(self) -> str:
        return f"refresh_{self.id}"

    def get_refresh_target(self) -> str:
        return f"#{self.id}"

    def get_refresh_swap(self) -> str:
        return "outerHTML"

    def get_refresh_command(self) -> str:
        return f"{self.get_refresh_event()} from:body"

    def configure(self) -> None:
        (
            self.htmx.get(self.url)
            .target_to(self.get_refresh_target())
            .trigger_on(self.get_refresh_command())
            .swap_to(self.get_refresh_swap())
        )

    def refresh_widget(self) -> Response:
        return self.response().emit(self.get_refresh_event())

    # ------------------------------------------------------------------
    # Caching
    # ------------------------------------------------------------------

    def should_cache(self) -> bool:
        return self.cache_timeout is not None

    def cache_key(self) -> str:
        return ":".join(
            (
                self.namespace,
                self.identifier,
                self.cache_identifier(),
                self.generate_state_hash(),
            )
        )

    def cache_identifier(self) -> str:
        user = self.user

        if user and user.is_authenticated:
            return str(user.pk)

        return "anonymous"

    def generate_state_hash(self) -> str:
        return "default"

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def get_context(self) -> dict[str, Any]:
        """
        Extend the generic Component context with the widget reference.
        """
        context = super().get_context()
        context["widget"] = self
        return context

    # ------------------------------------------------------------------
    # HTTP responses
    # ------------------------------------------------------------------

    def response(self) -> Response:
        return Response.html(
            self.render_to_string()
        )

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

    # ------------------------------------------------------------------
    # URL dispatch
    # ------------------------------------------------------------------

    def dispatch_url(self):
        return safe_reverse(
            view_name="widget_view",
            namespace=self.namespace,
            kwargs={
                "app_name": self.identity.app_name,
                "class_name": self.identity.class_name,
            },
        )
