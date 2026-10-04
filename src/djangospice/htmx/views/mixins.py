from __future__ import annotations

from typing import Any

from djangospice.htmx.response import Response

class HTMXTemplateMixin:
    """
    Adds HTMX-aware template rendering to an existing Django CBV.

    Normal requests are handled by Django's normal response machinery.

    HTMX requests return a Djangospice Response descriptor which is
    materialized by HTMXMiddleware.
    """

    htmx_template_name: str | None = None

    # ------------------------------------------------------------------
    # HTMX
    # ------------------------------------------------------------------

    def is_htmx(self) -> bool:
        return bool(self.request.htmx)

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------

    def get_htmx_template_name(self) -> str:
        if not self.htmx_template_name:
            raise AttributeError(
                f"{self.__class__.__name__} requires "
                "'htmx_template_name' when handling an HTMX request."
            )

        return self.htmx_template_name

    def get_template_names(self):
        """
        Allow Django internals and subclasses to resolve the appropriate
        template for the current request.
        """
        if self.is_htmx():
            return [self.get_htmx_template_name()]

        return super().get_template_names()

    # ------------------------------------------------------------------
    # Response
    # ------------------------------------------------------------------

    def render_to_response(
        self,
        context: dict[str, Any],
        **response_kwargs: Any,
    ):
        """
        Return a Djangospice Response for HTMX requests.

        Non-HTMX requests are delegated to the underlying Django CBV.
        """
        if not self.is_htmx():
            return super().render_to_response(
                context,
                **response_kwargs,
            )

        status = response_kwargs.pop("status", 200)

        return Response.render(
            self.get_htmx_template_name(),
            status=status,
            **context,
        )


class HTMXFormMixin:
    """
    Adds HTMX-specific form behavior while leaving Django's FormView,
    CreateView and UpdateView lifecycle intact.

    Normally no override is required because Django eventually calls
    render_to_response(), which HTMXTemplateMixin handles.

    This mixin exists as an extension point for applications that need
    additional form-specific HTMX behavior.
    """

    def get_form_context(
        self,
        form,
    ) -> dict[str, Any]:
        return {
            "form": form,
        }

    def get_invalid_form_context(
        self,
        form,
    ) -> dict[str, Any]:
        return self.get_form_context(form)

    def get_valid_form_context(
        self,
        form,
    ) -> dict[str, Any]:
        return self.get_form_context(form)


class HTMXModalMixin:
    """
    Provides modal configuration and modal lifecycle hooks.

    The mixin does not render the modal itself. HTMXModal is responsible
    for integrating the configuration into the response context.
    """

    modal_title: str | None = None
    modal_size: str | None = None
    modal_template_name: str | None = None

    save_button_text: str | None = None
    cancel_button_text: str | None = None

    modal_context_name: str = "modal"

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def get_modal_config(self) -> dict[str, Any]:
        return {
            "title": self.get_modal_title(),
            "size": self.get_modal_size(),
            "save_button_text": self.get_save_button_text(),
            "cancel_button_text": self.get_cancel_button_text(),
        }

    def get_modal_title(self) -> str | None:
        return self.modal_title

    def get_modal_size(self) -> str | None:
        return self.modal_size

    def get_save_button_text(self) -> str | None:
        return self.save_button_text

    def get_cancel_button_text(self) -> str | None:
        return self.cancel_button_text

    # ------------------------------------------------------------------
    # Template
    # ------------------------------------------------------------------

    def get_modal_template_name(self) -> str:
        if not self.modal_template_name:
            raise AttributeError(
                f"{self.__class__.__name__} requires "
                "'modal_template_name'."
            )

        return self.modal_template_name

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------

    def get_modal_context(self) -> dict[str, Any]:
        return {
            "modal_template_name": self.get_modal_template_name(),
            self.modal_context_name: self.get_modal_config(),
        }

    def update_modal_context(
        self,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        context.update(
            self.get_modal_context()
        )
        return context


class HTMXTabMixin:
    """
    Adds tab metadata and permission handling to any Django CBV.

    It does not define the underlying view behavior. Compose it with
    Django's View, DetailView, CreateView, UpdateView, etc.
    """

    tab_name: str = ""
    tab_label: str = ""
    is_primary: bool = False

    permission_required: str | None = None

    context_meta_name: str = "tab_meta"

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    def test_func(self) -> bool:
        if self.permission_required:
            return self.request.user.has_perm(
                self.permission_required
            )

        return True

    @classmethod
    def get_tab_name(cls) -> str:
        name = cls.tab_name

        if name:
            return name

        if cls.tab_label:
            from django.utils.text import slugify

            return slugify(cls.tab_label).replace(
                "-",
                "_",
            )

        return ""

    @classmethod
    def get_tab_label(cls) -> str:
        if cls.tab_label:
            return cls.tab_label

        if cls.tab_name:
            return (
                cls.tab_name
                .replace("_", " ")
                .replace("-", " ")
                .title()
            )

        return ""

    @classmethod
    def get_tab_metadata(cls) -> dict[str, Any]:
        return {
            "name": cls.get_tab_name(),
            "label": cls.get_tab_label(),
            "is_primary": cls.is_primary,
            "class": cls,
            "perm": cls.permission_required,
        }

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------

    def get_tab_context(
        self,
    ) -> dict[str, Any]:
        return {
            self.context_meta_name: self.get_tab_metadata(),
        }

    def get_context_data(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            self.get_tab_context()
        )

        return context


class HTMXSearchMixin:
    """
    Adds a simple query-string search contract to an existing list view.

    Applications can override apply_search() to implement their actual
    queryset search.
    """

    search_param = "q"
    search_placeholder = "Search..."

    def get_search_query(self) -> str:
        return self.request.GET.get(
            self.search_param,
            "",
        ).strip()

    def has_search_query(self) -> bool:
        return bool(
            self.get_search_query()
        )

    def apply_search(self, queryset):
        """
        Override this in the application.

        Example:

            def apply_search(self, queryset):
                query = self.get_search_query()

                if not query:
                    return queryset

                return queryset.filter(
                    name__icontains=query
                )
        """
        return queryset

    def get_queryset(self):
        queryset = super().get_queryset()

        return self.apply_search(
            queryset
        )

    def get_search_context(self) -> dict[str, Any]:
        query = self.get_search_query()

        return {
            "query": query,
            "has_query": bool(query),
            "placeholder": self.search_placeholder,
            "search_param": self.search_param,
        }

    def get_context_data(
        self,
        **kwargs: Any,
    ):
        context = super().get_context_data(
            **kwargs
        )

        context.update(
            self.get_search_context()
        )

        return context
