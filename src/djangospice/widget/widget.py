from __future__ import annotations

from typing import Any, ClassVar

from django.db.models import Model, QuerySet
from django.forms import BaseForm

from djangospice.exec.mixin import Executable
from djangospice.html.component import Component
from djangospice.http.headers import HTMXHeaders
from djangospice.http.response import Response
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
    app_view: ClassVar[str] = "app-view"

    lazy: ClassVar[bool] = True

    refreshable: ClassVar[bool] = False
    refresh_interval: ClassVar[int | None] = None

    cache_timeout: ClassVar[int | None] = None


    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    def get_skeleton(self):
        return None

    def has_skeleton(self):
        return bool(self.get_skeleton())

    def get_refresh_event(self) -> str:
        return f"refresh_{self.id}"

    def get_widget_target(self) -> str:
        return f"#{self.id}"

    def get_refresh_swap(self) -> str:
        return "outerHTML"

    def get_refresh_command(self) -> str:
        return f"{self.get_refresh_event()} from:body"

    def configure(self) -> None:
        (
            self.htmx.get(self.url)
            .target(self.get_widget_target())
            .trigger(self.get_refresh_command())
            .swap(self.get_refresh_swap())
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

    def get_context(self) -> dict[str, Any]:
        """
        Extend the generic Component context with the widget reference.
        """
        context = super().get_context()
        context["widget"] = self
        context["app_view"] = self.app_view
        return context

    def response(self,  content: str | bytes = b"",
        *,
        status: int = 200,
        content_type: str = "text/html; charset=utf-8",
        template: str | None = None,
        context: dict[str, Any] | None = None,
        htmx: HTMXHeaders | None = None,) -> Response:
        return Response(content, status=status, content_type=content_type, template=template, context=context, htmx=htmx)  

    def refresh(self) -> Response:
        return Response.from_content(
            self.render_to_string()
        )
    
    def get(self) -> Response:
        return Response.from_content(
            self.render_to_string()
        )

    def post(self) -> Response:
        return self.method_not_allowed()

    def put(self) -> Response:
        return self.method_not_allowed()

    def patch(self) -> Response:
        return self.method_not_allowed()

    def delete(self) -> Response:
        return self.method_not_allowed()

    def method_not_allowed(self) -> Response:
        return Response.create(status=405)

    def dispatch_url(self):
        return safe_reverse(
            view_name="widget_view",
            app_name=self.namespace,
            kwargs={
                "app_name": self.identity.app_name,
                "class_name": self.identity.class_name,
            },
        )


class DetailsWidget(Widget):
    """
    Widget equivalent to Django's DetailView.
    Supports memoization, explicit object/id injection, and lazy loading.
    """

    context_object_name: ClassVar[str | None] = None

    def __init__(self, *args, object_id: Any = None, object: Model | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._explicit_object_id = object_id
        self._explicit_object = object
        self._cached_object = None
        self._object_resolved = False

    def dispatch_url(self) -> str:
        """
        Ensures lazy-loading HTMX requests retain explicit object IDs.
        """
        url = super().dispatch_url()
        pk = self._explicit_object_id or (self._explicit_object.pk if self._explicit_object else None)
        if not pk:
            pk = self.get_value(self.object_parameter)
        
        if pk:
            separator = "&" if "?" in url else "?"
            url += f"{separator}{self.object_parameter}={pk}"
        return url

    def get_object(self) -> Model | None:
        if self._object_resolved:
            return self._cached_object

        self._object_resolved = True

        if self._explicit_object is not None:
            self._cached_object = self._explicit_object
            return self._cached_object

        pk = self._explicit_object_id or self.get_value(self.object_parameter)
        if not pk and self.request and self.request.resolver_match:
            pk = self.request.resolver_match.kwargs.get(self.object_parameter)

        if not pk:
            self._cached_object = None
            return None

        self._cached_object = self.get_queryset().filter(pk=pk).first()
        return self._cached_object

    def get_context_object_name(self) -> str:
        if self.context_object_name:
            return self.context_object_name
        if self.model is not None:
            return self.model._meta.model_name
        return "object"

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        obj = self.get_object()
        context[self.get_context_object_name()] = obj
        return context

    def get(self) -> Response:
        obj = self.get_object()
        if obj is None:
            return Response.create(status=404)
        return super.get()


class FormWidget(Widget):
    """
    Intermediate base class for Create and Update form widgets.
    Handles memoization, form setup, files, and state persistence.
    """

    form_class: ClassVar[type[BaseForm] | None] = None
    success_event: ClassVar[str | None] = None

    def __init__(self, *args, object_id: Any = None, instance: Model | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._explicit_object_id = object_id
        self._explicit_instance = instance
        self._cached_object = None
        self._object_resolved = False

    def dispatch_url(self) -> str:
        url = super().dispatch_url()
        pk = self._explicit_object_id or (self._explicit_instance.pk if self._explicit_instance else None)
        if not pk:
            pk = self.get_value(self.object_parameter)

        if pk:
            separator = "&" if "?" in url else "?"
            url += f"{separator}{self.object_parameter}={pk}"
        return url

    def get_object(self) -> Model | None:
        if self._object_resolved:
            return self._cached_object

        self._object_resolved = True

        if self._explicit_instance is not None:
            self._cached_object = self._explicit_instance
            return self._cached_object

        pk = self._explicit_object_id or self.get_value(self.object_parameter)
        if not pk and self.request and self.request.resolver_match:
            pk = self.request.resolver_match.kwargs.get(self.object_parameter)

        if not pk or not self.model:
            self._cached_object = None
            return None

        self._cached_object = self.model._default_manager.filter(pk=pk).first()
        return self._cached_object

    def get_form_class(self) -> type[BaseForm]:
        if self.form_class is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define 'form_class' or override 'get_form_class()'."
            )
        return self.form_class

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if self.request and self.request.method in {"POST", "PUT", "PATCH"}:
            kwargs.update({
                "data": self.request.POST,
                "files": self.request.FILES,
            })
        
        obj = self.get_object()
        if obj is not None:
            kwargs["instance"] = obj

        return kwargs

    def get_form(self, form_class: type[BaseForm] | None = None) -> BaseForm:
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        if "form" not in context:
            context["form"] = self.get_form()
        return context


class CreateWidget(FormWidget):
    """
    Widget equivalent to Django's CreateView.
    """

    def form_valid(self, form: BaseForm) -> Response:
        self.object = form.save()
        response = self.response()
        if self.success_event:
            response = response.trigger(self.success_event)
        return response.trigger(self.get_refresh_event())

    def form_invalid(self, form: BaseForm) -> Response:
        context = self.get_context()
        context["form"] = form
        return Response.html(self.render_to_string(), status=422)

    def post(self) -> Response:
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)


class UpdateWidget(FormWidget):
    """
    Widget equivalent to Django's UpdateView.
    """

    def get(self) -> Response:
        obj = self.get_object()
        if obj is None:
            return Response.create(status=404)
        return super.get()

    def form_valid(self, form: BaseForm) -> Response:
        self.object = form.save()
        response = self.response()
        if self.success_event:
            response = response.trigger(self.success_event)
        return response.trigger(self.get_refresh_event())

    def form_invalid(self, form: BaseForm) -> Response:
        context = self.get_context()
        context["form"] = form
        return Response.html(self.render_to_string(), status=422)

    def post(self) -> Response:
        obj = self.get_object()
        if obj is None:
            return Response.create(status=404)
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def put(self) -> Response:
        return self.post()

    def patch(self) -> Response:
        return self.post()