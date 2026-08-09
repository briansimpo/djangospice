from __future__ import annotations

from abc import ABC
from typing import Any, ClassVar, TYPE_CHECKING

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.http import HttpRequest

from djangospice.html.component import HTMLComponent
from djangospice.response.response import Response

from djangospice.widgets.metadata import WidgetMetaclass
from djangospice.widgets.metadata import (
    WidgetCacheMixin,
    WidgetDataMixin,
    WidgetHTMXMixin,
    WidgetHttpMixin, 
    WidgetMetadataMixin,
    WidgetVisibilityMixin
)

if TYPE_CHECKING:
    from djangospice.widgets.actions import ActionCollection


class Widget(
    WidgetMetadataMixin,
    WidgetHTMXMixin,
    WidgetVisibilityMixin,
    WidgetDataMixin,
    WidgetHttpMixin,
    WidgetCacheMixin,
    HTMLComponent,
    ABC,
    metaclass=WidgetMetaclass
):

    namespace: str = "djangospice_widget"
    actions: ClassVar[ActionCollection]

    def __init__(self, request: HttpRequest | None = None, **kwargs: Any) -> None:
        super().__init__(kwargs=kwargs)
        self.request = request
        self.template_name = self._meta.template_name or self.template_name

    @property
    def user(self) -> AbstractBaseUser | AnonymousUser | None:
        return getattr(self.request, "user", None)

    def initialize(self) -> None:
        """Called immediately after widget construction."""
        pass

    def configure(self) -> None:
        """Configure widget state."""
        pass

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        context.update(widget=self, request=self.request)
        return context

    def response(self) -> Response:
        return Response.make(self.template_name, **self.get_context())

