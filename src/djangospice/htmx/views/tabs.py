from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.shortcuts import render
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin

from .mixins import (
    HTMXTabMixin,
    HTMXTemplateMixin,
)
from djangospice.htmx.response import Response


# ============================================================================
# TAB VIEWS
# ============================================================================


class HTMXTemplateTabView(HTMXTabMixin, HTMXTemplateMixin, View):
    """
    Object-less HTMX tab.

    Suitable for:
    - settings
    - statistics
    - summaries
    - dashboards
    - general information
    """

    pass


class HTMXDetailTabView(
    HTMXTabMixin,
    HTMXTemplateMixin,
    DetailView,
):
    """
    Object-backed HTMX tab.
    """

    model = None


class HTMXCreateTabView(
    HTMXTabMixin,
    HTMXTemplateMixin,
    CreateView,
):
    """
    Create-form HTMX tab.
    """

    pass


class HTMXUpdateTabView(
    HTMXTabMixin,
    HTMXTemplateMixin,
    UpdateView,
):
    """
    Update-form HTMX tab.
    """

    pass


class HTMXDeleteTabView(
    HTMXTabMixin,
    SingleObjectMixin,
    View,
):
    """
    Delete endpoint for a tab.

    DELETE and POST are both supported.
    """

    model = None

    def delete(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        self.object = self.get_object()

        self.delete_object()

        return self.get_delete_response()

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        return self.delete(
            request,
            *args,
            **kwargs,
        )

    def delete_object(self) -> None:
        self.object.delete()

    def get_delete_response(self) -> Response:
        return Response.empty().trigger("refreshTab")


# ============================================================================
# TAB CONTAINER
# ============================================================================


class HTMXTabContainerView(View):
    """
    Coordinates a collection of HTMX tabs.

    Responsibilities:
        - discover tabs
        - filter tabs by permissions
        - resolve the active tab
        - persist active-tab state
        - dispatch HTMX requests to the active tab
        - render the full tab container

    Individual tabs remain normal Django CBVs.
    """

    template_name: str | None = None

    tab_classes: list[type[HTMXTabMixin]] = []

    param_name = "tab"

    title: str | None = None

    # Set this when the container represents an object.
    model = None

    # ------------------------------------------------------------------
    # Tab configuration
    # ------------------------------------------------------------------

    @classmethod
    def get_tab_session_key(cls) -> str:
        return f"active_tab_{cls.__name__}"

    def get_tab_classes(
        self,
    ) -> list[type[HTMXTabMixin]]:
        return list(self.tab_classes)

    # ------------------------------------------------------------------
    # Permissions / visibility
    # ------------------------------------------------------------------

    def get_visible_tabs(
        self,
        request: HttpRequest,
    ) -> list[dict[str, Any]]:
        visible: list[dict[str, Any]] = []

        for tab_class in self.get_tab_classes():
            permission = tab_class.permission_required

            if permission:
                if not request.user.has_perm(permission):
                    continue

            visible.append(
                tab_class.get_tab_metadata()
            )

        return visible

    # ------------------------------------------------------------------
    # Requested tab
    # ------------------------------------------------------------------

    def get_requested_tab_name(
        self,
        request: HttpRequest,
    ) -> str | None:
        """
        Resolve explicit tab selection.

        POST takes precedence over GET, followed by the session.
        """

        name = request.POST.get(
            self.param_name
        )

        if name:
            return name

        name = request.GET.get(
            self.param_name
        )

        if name:
            return name

        return request.session.get(
            self.get_tab_session_key()
        )

    # ------------------------------------------------------------------
    # Default tab
    # ------------------------------------------------------------------

    def get_default_tab(
        self,
        visible_tabs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        primary = next(
            (
                tab
                for tab in visible_tabs
                if tab["is_primary"]
            ),
            None,
        )

        return primary or visible_tabs[0]

    # ------------------------------------------------------------------
    # Active tab
    # ------------------------------------------------------------------

    def resolve_active_tab(
        self,
        request: HttpRequest,
        visible_tabs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        requested_name = (
            self.get_requested_tab_name(request)
        )

        active = next(
            (
                tab
                for tab in visible_tabs
                if tab["name"] == requested_name
            ),
            None,
        )

        if active is None:
            active = self.get_default_tab(
                visible_tabs
            )

        request.session[
            self.get_tab_session_key()
        ] = active["name"]

        return active

    # ------------------------------------------------------------------
    # Parent object
    # ------------------------------------------------------------------

    def get_parent_object(self) -> Any | None:
        """
        Resolve the object represented by the tab container.

        Subclasses can override this when the parent object is resolved
        differently.
        """

        if self.model is None:
            return None

        resolver = SingleObjectMixin()
        resolver.model = self.model
        resolver.kwargs = self.kwargs

        return resolver.get_object()

    # ------------------------------------------------------------------
    # Tab view
    # ------------------------------------------------------------------

    def get_tab_view(
        self,
        tab_class: type[HTMXTabMixin],
    ):
        return tab_class()

    def prepare_tab_view(
        self,
        request: HttpRequest,
        tab_class: type[HTMXTabMixin],
        parent_object: Any | None,
        **kwargs: Any,
    ):
        """
        Prepare a tab instance for rendering inside the container.
        """

        tab_view = self.get_tab_view(
            tab_class
        )

        tab_view.setup(
            request,
            **kwargs,
        )

        if parent_object is not None:
            tab_view.object = parent_object

        if not tab_view.test_func():
            raise PermissionDenied

        return tab_view

    # ------------------------------------------------------------------
    # Container context
    # ------------------------------------------------------------------

    def get_container_context(
        self,
    ) -> dict[str, Any]:
        return {}

    def get_context_data(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        context = {
            "title": self.title,
        }

        context.update(
            self.get_container_context()
        )

        context.update(kwargs)

        return context

    # ------------------------------------------------------------------
    # Full-page rendering
    # ------------------------------------------------------------------

    def render_container(
        self,
        request: HttpRequest,
        *,
        parent_object: Any | None,
        visible_tabs: list[dict[str, Any]],
        active_tab: dict[str, Any],
        tab_context: dict[str, Any],
    ):
        context = self.get_context_data(
            **tab_context,
            container_object=parent_object,
            tabs=visible_tabs,
            active_tab=active_tab,
            active_tab_session_key=(
                self.get_tab_session_key()
            ),
            tab_param=self.param_name,
        )

        return render(
            request,
            self.template_name,
            context,
        )

    # ------------------------------------------------------------------
    # Request
    # ------------------------------------------------------------------

    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ):
        visible_tabs = self.get_visible_tabs(
            request
        )

        if not visible_tabs:
            raise PermissionDenied(
                "No authorized tabs available."
            )

        parent_object = (
            self.get_parent_object()
        )

        active_tab = self.resolve_active_tab(
            request,
            visible_tabs,
        )

        tab_class = active_tab["class"]

        # --------------------------------------------------------------
        # HTMX request
        # --------------------------------------------------------------

        if request.htmx:
            return tab_class.as_view()(
                request,
                *args,
                **kwargs,
            )

        # --------------------------------------------------------------
        # Normal request
        # --------------------------------------------------------------

        tab_view = self.prepare_tab_view(
            request,
            tab_class,
            parent_object,
            **kwargs,
        )

        tab_context = tab_view.get_context_data(
            **kwargs,
        )

        return self.render_container(
            request,
            parent_object=parent_object,
            visible_tabs=visible_tabs,
            active_tab=active_tab,
            tab_context=tab_context,
        )


class HTMXObjectTabContainerView(
    SingleObjectMixin,
    HTMXTabContainerView,
):
    """
    Tab container whose tabs belong to a parent object.

    This allows the container itself to use Django's SingleObjectMixin
    object resolution.
    """

    model = None

    def get_parent_object(self) -> Any | None:
        return self.get_object()