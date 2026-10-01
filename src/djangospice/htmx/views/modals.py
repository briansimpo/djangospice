from __future__ import annotations

from typing import Any

from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    UpdateView,
)

from .mixins import (
    HTMXFormMixin,
    HTMXModalMixin,
    HTMXTemplateMixin,
)

from djangospice.templates import get_template_name
from djangospice.htmx.response import Response
from djangospice.htmx.apps import namespace

class HTMXModal(
    HTMXModalMixin,
    HTMXTemplateMixin,
    View,
):
    """
    Base HTMX modal.

    The modal itself is just another HTMX template response.
    """

    htmx_template_name = get_template_name("modal/modal.html", namespace)

    def get_context_data(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        context = dict(kwargs)

        self.update_modal_context(
            context
        )

        return context


class HTMXFormModal(
    HTMXFormMixin,
    HTMXModal,
):
    """
    Base form modal.

    Designed to compose with Django's FormView, CreateView or
    UpdateView.
    """

    def get_context_data(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        context = super().get_context_data(
            **kwargs
        )

        if "form" not in context:
            context["form"] = self.get_form()

        return context

    def get_success_url(self) -> str:
        return self.request.path


class HTMXCreateModal(
    HTMXFormModal,
    CreateView,
):
    """
    HTMX modal backed by Django CreateView.
    """

    pass


class HTMXUpdateModal(
    HTMXFormModal,
    UpdateView,
):
    """
    HTMX modal backed by Django UpdateView.
    """

    pass


class HTMXDeleteModal(
    HTMXModal,
    DeleteView,
):
    """
    HTMX confirmation modal backed by Django DeleteView.
    """

    modal_title = "Confirm Deletion"
    save_button_text = "Yes, Delete"

    def delete(
        self,
        request,
        *args,
        **kwargs,
    ) -> Response:
        self.object = self.get_object()

        self.delete_object()

        return self.get_delete_response()

    def delete_object(self) -> None:
        self.object.delete()

    def get_delete_response(self) -> Response:
        return Response.empty().refresh_data()



class HTMXObjectModal(
    HTMXModalMixin,
    HTMXTemplateMixin,
    View,
):
    """
    Base object-aware modal.

    Useful when a modal needs an object but does not itself need
    CreateView/UpdateView/DeleteView semantics.
    """

    htmx_template_name = get_template_name("modal/modal.html", namespace)

    def get_context_data(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        context = dict(kwargs)

        self.update_modal_context(
            context
        )

        return context