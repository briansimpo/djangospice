from __future__ import annotations

from copy import deepcopy
from typing import Any, ClassVar


from django.core.exceptions import  PermissionDenied
from django.db.models import Model, QuerySet
from django.http import HttpRequest

from djangospice.core.executable import Executable
from djangospice.htmx.component import HTMLComponent
from djangospice.htmx.response import Response
from djangospice.utils import safe_reverse

from .actions import Action, ActionContext, Actions, BoundAction
from .exceptions import WidgetNotVisible
from .apps import namespace


class Widget(Executable, HTMLComponent):
    """ 
    Base class for Djangospice UI widgets.

    A Widget coordinates:

    - identity and registration metadata
    - presentation and rendering
    - request state
    - permissions and visibility
    - actions
    - child widgets and slots
    - model/queryset resolution
    - navigation and HTMX interactions
    - caching
    - HTTP response generation

    Rendering itself is delegated to ``HTMLComponent``. A widget may
    therefore render either:

    1. through ``template_name`` + ``get_context()``, or
    2. through ``get_content()`` for direct HTML content.
    """

    # ------------------------------------------------------------------
    # Class Attributes & Configuration
    # ------------------------------------------------------------------

    description: ClassVar[str] = ""
    suffix: ClassVar[str] = "Widget"

    actions: ClassVar[Actions] = Actions()
    _actions: ClassVar[Actions] = Actions()

    enabled: ClassVar[bool] = True
    permission: ClassVar[str | None] = None
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

    login_required: ClassVar[bool] = False
    staff_required: ClassVar[bool] = False
    permissions: ClassVar[tuple[str, ...]] = ()

    # ------------------------------------------------------------------
    # Initialization & Subclass Configuration
    # ------------------------------------------------------------------

    def __init__(
        self,
        request: HttpRequest | None = None,
        *,
        parent: Widget | None = None,
        children: list[Widget] | None = None,
        slots: dict[str, list[Widget]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(request=request, **kwargs)

        self.parent = parent
        self.children: list[Widget] = []
        self.slots: dict[str, list[Widget]] = {}

        self.add_children(*(children or []))

        for name, widgets in (slots or {}).items():
            self.set_slot(name, *widgets)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        cls._normalize_actions()

    def initialize(self):
        pass

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    @classmethod
    def _declared_action_groups(cls) -> dict[str, Actions]:
        groups: dict[str, Actions] = {}

        for base in reversed(cls.__mro__):
            for name, value in base.__dict__.items():
                if isinstance(value, Actions):
                    groups[name] = value

        return groups

    @classmethod
    def _normalize_actions(cls) -> None:
        groups = cls._declared_action_groups()
        normalized: dict[str, Actions] = {}

        for name, actions in groups.items():
            if (
                name in cls.__dict__
                and isinstance(cls.__dict__[name], Actions)
            ):
                collection = Actions(*deepcopy(actions))
                setattr(cls, name, collection)
                normalized[name] = collection
            else:
                normalized[name] = actions

        cls._actions = cls.merge_actions(*normalized.values())

    @classmethod
    def merge_actions(cls, *collections: Actions) -> Actions:
        actions: dict[str, Any] = {}

        for collection in collections:
            for action in collection:
                actions[action.name] = deepcopy(action)

        return Actions(*actions.values())

    def get_action_collection(self) -> Actions:
        return self._actions

    def bind_action(self, action: Action, context: ActionContext) -> BoundAction:
        return BoundAction(
            action=action,
            context=context,
        )

    # ------------------------------------------------------------------
    # Composition & Tree Hierarchy
    # ------------------------------------------------------------------

    def add_child(self, widget: Widget) -> Widget:
        self._attach(widget)
        self.children.append(widget)
        return widget

    def add_children(self, *widgets: Widget) -> tuple[Widget, ...]:
        for widget in widgets:
            self.add_child(widget)

        return widgets

    def remove_child(self, widget: Widget) -> None:
        if widget not in self.children:
            return

        self.children.remove(widget)

        if widget.parent is self:
            widget.parent = None

    def clear_children(self) -> None:
        for widget in self.children:
            if widget.parent is self:
                widget.parent = None

        self.children.clear()

    def get_children(self) -> tuple[Widget, ...]:
        return tuple(self.children)

    def set_slot(self, name: str, *widgets: Widget) -> None:
        self.clear_slot(name)

        for widget in widgets:
            self.add_to_slot(name, widget)

    def add_to_slot(self, name: str, widget: Widget) -> Widget:
        self._attach(widget)
        self.slots.setdefault(name, []).append(widget)
        return widget

    def add_to_slots(self, **slots: Widget | list[Widget] | tuple[Widget, ...]) -> None:
        for name, value in slots.items():
            if isinstance(value, Widget):
                self.add_to_slot(name, value)
                continue

            for widget in value:
                self.add_to_slot(name, widget)

    def get_slot(self, name: str) -> tuple[Widget, ...]:
        return tuple(self.slots.get(name, ()))

    def has_slot(self, name: str) -> bool:
        return bool(self.slots.get(name))

    def remove_from_slot(self, name: str, widget: Widget) -> None:
        widgets = self.slots.get(name)

        if not widgets or widget not in widgets:
            return

        widgets.remove(widget)

        if widget.parent is self:
            widget.parent = None

    def clear_slot(self, name: str) -> None:
        for widget in self.slots.get(name, ()):
            if widget.parent is self:
                widget.parent = None

        self.slots.pop(name, None)

    def clear_slots(self) -> None:
        for name in tuple(self.slots):
            self.clear_slot(name)

    def _attach(self, widget: Widget) -> None:
        if widget is self:
            raise ValueError(
                "A widget cannot contain itself.",
            )

        widget.parent = self

        if widget.request is None:
            widget.request = self.request

    # ------------------------------------------------------------------
    # Request & Visibility
    # ------------------------------------------------------------------
    @property
    def is_lazy_fetch(self) -> bool:
        request = self.request

        if (request is None or request.headers.get("HX-Request") != "true"):
            return False

        match = request.resolver_match

        return bool(
            match
            and match.view_name == self.namespace
            and match.kwargs.get("app_name") == self.app_name
            and match.kwargs.get("class_name") == self.class_name
        )
    
    @property
    def request_data(self) -> Any:
        if self.request is None:
            return None

        if self.request.method in {"POST", "PUT", "PATCH"}:
            return self.request.POST

        return self.request.GET

    def request_value(self, name: str) -> Any:
        data = self.request_data

        if data is None:
            return None

        return data.get(name)

    def request_values(self, name: str) -> list[Any]:
        data = self.request_data

        if data is None:
            return []

        return data.getlist(name)

    def authorize(self) -> None:
        user = self.user

        if not self.visible():
            raise WidgetNotVisible

        if self.login_required and not user.is_authenticated:
            raise PermissionDenied

        if self.staff_required and not user.is_staff:
            raise PermissionDenied

        if self.permissions and not user.has_perms(self.permissions):
            raise PermissionDenied

    def visible(self) -> bool:
        if not self.enabled:
            return False

        if self.permission and not self._has_permission():
            return False

        return self.is_visible()

    def _has_permission(self) -> bool:
        user = self.user

        return bool(
            user
            and user.is_authenticated
            and user.has_perm(self.permission),
        )

    def is_visible(self) -> bool:
        return True

    # ------------------------------------------------------------------
    # Data Resolution
    # ------------------------------------------------------------------

    def get_queryset(self) -> QuerySet[Model]:
        if self.model is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define "
                "'model' or override 'get_queryset()'.",
            )

        return self.model._default_manager.all()

    def get_object(self) -> Model | None:
        pk = self.request_value(self.object_parameter)

        if not pk:
            return None

        return self.get_queryset().filter(pk=pk).first()

    def get_objects(self) -> tuple[Model, ...]:
        ids = self.request_values(self.objects_parameter)

        if not ids:
            obj = self.get_object()
            return (obj,) if obj else ()

        return tuple(
            self.get_queryset().filter(pk__in=ids),
        )

    def get_data(self) -> dict:
        return self.request_data

    def get_refresh_event(self) -> str:
        return f"refresh_{self.id}"

    def get_refresh_target(self) -> str:
        return "this"

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
            ),
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
        Extend HTMLComponent context with widget-specific values.
        """
        context = super().get_context()

        context.update(
            widget=self,
            request=self.request,
            children=self.get_children(),
            slots=self.slots,
        )

        return context

    def render(self, request: HttpRequest | None = None) -> Any:
        """
        Render the widget through the HTMLComponent pipeline.

        HTMLComponent decides whether rendering happens through:

        - ``get_content()``, or
        - ``template_name`` + ``get_context()``.
        """
        actual_request = (
            request
            if request is not None
            else self.request
        )

        return super().render(
            request=actual_request,
        )

    # ------------------------------------------------------------------
    # HTTP Response & Methods
    # ------------------------------------------------------------------

    def response(self) -> Response:
        """
        Build the HTTP response containing the widget's rendered HTML.

        Rendering is intentionally performed by ``HTMLComponent`` rather
        than duplicating template/content resolution here.
        """
        return Response.content(
            self.render(request=self.request),
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

    def dispatch_url(self):
        return safe_reverse(
            view_name="widget_view",
            namespace=self.namespace,
            kwargs={
                "app_name": self.identity.app_name,
                "class_name": self.identity.class_name,
            },
        )
    
