from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar
from urllib.parse import urlencode

from django.urls import reverse

from djangospice.core.payload import Payload
from djangospice.response.response import Response
from djangospice.widgets.exceptions import WidgetNotVisible

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
    from django.db.models import Model, QuerySet
    from django.http import HttpRequest
    from .options import WidgetOptions
    

class WidgetMetadataMixin:
    """Provides declarative metadata properties derived from _meta."""
    _meta: ClassVar[WidgetOptions]
    kwargs: dict[str, Any]
    
    @property
    def name(self) -> str: return self._meta.name

    @property
    def app_label(self) -> str: return self._meta.app_label

    @property
    def title(self) -> str: return self._meta.title

    @property
    def description(self) -> str: return self._meta.description

    @property
    def group(self) -> str | None: return self._meta.group

    @property
    def enabled(self) -> bool: return self._meta.enabled

    @property
    def permission(self) -> str | None: return self._meta.permission

    @property
    def priority(self) -> int: return self._meta.priority

    @property
    def lazy(self) -> bool: return self._meta.lazy

    @property
    def refreshable(self) -> bool: return self._meta.refreshable

    @property
    def refresh_interval(self) -> int | None: return self._meta.refresh_interval

    @property
    def cache_timeout(self) -> int | None: return self._meta.cache_timeout

    @property
    def cache_enabled(self) -> bool: return self.cache_timeout is not None

    @property
    def widget_key(self) -> str:
        return f"{self.app_label}.{self.name}" if self.app_label else self.name


class WidgetHTMXMixin:
    """Handles HTMX configuration and lazy fetching state."""
    namespace: str
    request: HttpRequest | None
    htmx: Any 

    @property
    def endpoint(self) -> str:
        url = reverse(self.namespace, kwargs={"app_label": self.app_label, "name": self.name})
        params = {k: v for k, v in self.kwargs.items() if k != "id"}
        return f"{url}?{urlencode(params)}" if params else url

    @property
    def is_lazy_fetch(self) -> bool:
        if not self.request or self.request.headers.get("HX-Request") != "true":
            return False
        match = self.request.resolver_match
        return bool(
            match
            and match.view_name == self.namespace
            and match.kwargs.get("app_label") == self.app_label
            and match.kwargs.get("name") == self.name
        )

    def configure_htmx(self) -> None:
        if self.lazy:
            self.htmx.get(self.endpoint).trigger_on("load").target_to("this").swap_to("outerHTML")

        if self.refreshable and self.refresh_interval:
            trigger = getattr(self.htmx, "trigger", "load") or "load"
            self.htmx.trigger_on(f"{trigger}, every {self.refresh_interval}s").target_to("this")


class WidgetVisibilityMixin:
    """Manages access control and visibility rules."""
    user: AbstractBaseUser | AnonymousUser | None

    def authorize(self) -> None:
        if not self.visible():
            raise WidgetNotVisible

    def visible(self) -> bool:
        if not self.enabled:
            return False

        if self.permission:
            user = self.user
            if not user or not user.is_authenticated or not user.has_perm(self.permission):
                return False

        return self.is_visible()

    def is_visible(self) -> bool:
        """Override for application-specific visibility rules."""
        return True


class WidgetDataMixin:
    """Handles data retrieval and queryset configuration."""
    request: HttpRequest | None
    _meta: ClassVar[WidgetOptions]

    def get_queryset(self) -> QuerySet[Model]:
        if self._meta.model is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define 'model' in Meta "
                "or override get_queryset()."
            )
        return self._meta.model._default_manager.all()

    def get_object(self) -> Model | None:
        if self.request is None:
            return None
            
        pk = (
            self.request.POST.get(self._meta.object_parameter)
            or self.request.GET.get(self._meta.object_parameter)
        )
        return self.get_queryset().filter(pk=pk).first() if pk else None

    def get_objects(self) -> tuple[Model, ...]:
        if self.request is None:
            return ()
            
        ids = (
            self.request.POST.getlist(self._meta.objects_parameter)
            or self.request.GET.getlist(self._meta.objects_parameter)
        )
        if not ids:
            obj = self.get_object()
            return (obj,) if obj else ()
            
        return tuple(self.get_queryset().filter(pk__in=ids))

    def get_data(self) -> Payload:
        if self.request is None:
            return Payload()

        if self.request.method in ("POST", "PUT", "PATCH"):
            return Payload.from_dict(self.request.POST.dict())
        return Payload.from_dict(self.request.GET.dict())


class WidgetHttpMixin:
    """Handles HTTP method routing."""
    def get(self) -> Response: return self.response()
    def post(self) -> Response: return self.method_not_allowed()
    def put(self) -> Response: return self.method_not_allowed()
    def patch(self) -> Response: return self.method_not_allowed()
    def delete(self) -> Response: return self.method_not_allowed()

    def method_not_allowed(self) -> Response:
        return Response.empty(status=405)


class WidgetCacheMixin:
    """Handles caching strategies."""
    namespace: str
    widget_key: str
    user: AbstractBaseUser | AnonymousUser | None

    def should_cache(self) -> bool:
        return getattr(self, "cache_enabled", False)

    def cache_key(self) -> str:
        identifier = str(self.user.pk) if self.user and self.user.is_authenticated else "anonymous"
        state_hash = getattr(self, "_generate_state_hash", lambda: "default")()
        return f"{self.namespace}:{self.widget_key}:{identifier}:{state_hash}"



