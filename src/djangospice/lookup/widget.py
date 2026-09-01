# djangospice/ui/widgets/lookup.py

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django import forms
from django.db import models
from django.urls import reverse

from djangospice.lookup.definition import LookupDefinition
from djangospice.lookup.dependencies import (
    LookupDependencyResolver,
)


class LookupWidget(forms.Select):
    """
    Django form widget backed by the DjangoSpice Lookup API.

    The widget remains a standard Django Select widget while adding
    DjangoSpice lookup metadata for Select2/AJAX integration.

    It can therefore be used with:

        ModelChoiceField
        ModelMultipleChoiceField
        ChoiceField
        TypedChoiceField
        django-filter

    Example:

        course = forms.ModelChoiceField(
            queryset=Course.objects.all(),
            widget=LookupWidget(
                model=Course,
            ),
        )

    Cascading:

        course = forms.ModelChoiceField(
            queryset=Course.objects.all(),
            widget=LookupWidget(
                model=Course,
                depends_on=(
                    Program,
                    "program__department",
                ),
            ),
        )
    """

    def __init__(
        self,
        attrs: dict[str, Any] | None = None,
        choices: Iterable | None = (),
        *,
        model: type[models.Model] | None = None,
        definition: LookupDefinition | None = None,
        depends_on: (
            str
            | type[models.Model]
            | Iterable[str | type[models.Model]]
            | None
        ) = None,
        placeholder: str = "Select...",
        search_placeholder: str = "Search...",
        page_size: int = 20,
        min_search_length: int = 0,
        allow_clear: bool = True,
        url: str | None = None,
        multi_select: bool | None = None,
        **kwargs: Any,
    ) -> None:

        if definition is not None:
            if (
                model is not None
                and model is not definition.model
            ):
                raise ValueError(
                    "model and definition.model must refer "
                    "to the same model."
                )

            model = definition.model

        if model is None:
            raise ValueError(
                "LookupWidget requires either "
                "model or definition."
            )

        if definition is not None:
            dependencies = definition.depends_on

            if depends_on is not None:
                dependencies = depends_on
        else:
            dependencies = (
                ()
                if depends_on is None
                else depends_on
            )

        self.model = model
        self.definition = definition

        self.depends_on = self.normalize_depends_on(
            dependencies
        )

        self.dependencies = (
            LookupDependencyResolver.normalize(
                model,
                self.depends_on,
            )
        )

        self.placeholder = placeholder
        self.search_placeholder = search_placeholder

        self.page_size = self.validate_page_size(
            page_size
        )

        self.min_search_length = (
            self.validate_min_search_length(
                min_search_length
            )
        )

        self.allow_clear = allow_clear

        self.lookup_url = (
            url or self.get_lookup_url()
        )

        self.multi_select = (
            multi_select
        )

        super().__init__(
            attrs=attrs,
            choices=choices,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_depends_on(
        depends_on,
    ) -> tuple[
        str | type[models.Model],
        ...
    ]:
        if depends_on is None:
            return ()

        if isinstance(
            depends_on,
            (str, type),
        ):
            return (depends_on,)

        return tuple(depends_on)

    @staticmethod
    def validate_page_size(
        page_size: int,
    ) -> int:
        if page_size <= 0:
            raise ValueError(
                "page_size must be greater than zero."
            )

        return page_size

    @staticmethod
    def validate_min_search_length(
        value: int,
    ) -> int:
        if value < 0:
            raise ValueError(
                "min_search_length cannot be negative."
            )

        return value

    def get_lookup_url(self) -> str:
        return reverse(
            "djangospice_lookup",
            kwargs={
                "app_label": (
                    self.model._meta.app_label
                ),
                "model_name": (
                    self.model._meta.model_name
                ),
            },
        )

    # ------------------------------------------------------------------
    # Select behaviour
    # ------------------------------------------------------------------

    def use_required_attribute(
        self,
        initial,
    ) -> bool:
        """
        Preserve Django's normal Select behaviour.

        LookupWidget must not interfere with Django's
        required-field semantics.
        """
        return super().use_required_attribute(
            initial
        )

    def format_value(self, value):
        """
        Preserve Django's normal value handling.

        This is important for:

            ModelChoiceField
            ModelMultipleChoiceField
            initial values
            bound forms
        """
        return super().format_value(value)

    # ------------------------------------------------------------------
    # HTML attributes
    # ------------------------------------------------------------------

    def get_lookup_dependencies(self) -> tuple[str, ...]:
        return tuple(
            dependency.path
            for dependency in self.dependencies
        )

    def get_multi_select(
        self,
        context: dict[str, Any],
    ) -> bool:
        if self.multi_select is not None:
            return self.multi_select

        return bool(
            context.get("widget", {}).get(
                "attrs",
                {},
            ).get("multiple")
        )

    def build_attrs(
        self,
        base_attrs: dict[str, Any] | None = None,
        extra_attrs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        attrs = super().build_attrs(
            base_attrs,
            extra_attrs,
        )

        attrs.update({
            "data-djangospice-lookup": "",
            "data-lookup-url": self.lookup_url,
            "data-lookup-page-size": str(
                self.page_size
            ),
            "data-lookup-min-search-length": str(
                self.min_search_length
            ),
            "data-lookup-placeholder": (
                self.placeholder
            ),
            "data-lookup-search-placeholder": (
                self.search_placeholder
            ),
            "data-lookup-allow-clear": (
                "true"
                if self.allow_clear
                else "false"
            ),
        })

        dependencies = (
            self.get_lookup_dependencies()
        )

        if dependencies:
            attrs[
                "data-lookup-dependencies"
            ] = ",".join(dependencies)

        return attrs

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------

    def get_context(
        self,
        name: str,
        value,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:

        context = super().get_context(
            name,
            value,
            attrs,
        )

        widget = context["widget"]

        widget["lookup"] = {
            "model": self.model,
            "definition": self.definition,

            "url": self.lookup_url,

            "dependencies": (
                self.dependencies
            ),

            "dependency_paths": (
                self.get_lookup_dependencies()
            ),

            "placeholder": (
                self.placeholder
            ),

            "search_placeholder": (
                self.search_placeholder
            ),

            "page_size": (
                self.page_size
            ),

            "min_search_length": (
                self.min_search_length
            ),

            "allow_clear": (
                self.allow_clear
            ),

            "multi_select": (
                self.multi_select
            ),
        }

        return context

