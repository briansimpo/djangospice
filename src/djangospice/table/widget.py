
from __future__ import annotations

from string import ascii_uppercase
from typing import Any, ClassVar

import django_filters
import django_tables2 as tables

from djangospice.utils import get_template_name
from djangospice.widget.widget import Widget
from djangospice.widget.actions import Actions
from djangospice.widget.composers import (
    ActionComposer,
    FilterComposer,
    SearchComposer,
)

from djangospice.table.fields import TableField

from .apps import namespace
from .composers import TableComposer


class TableWidget(Widget):
    """A configurable, server-rendered django-tables2 widget."""

    template_name = get_template_name("table.html", namespace)

    # ------------------------------------------------------------------
    # TABLE
    # ------------------------------------------------------------------

    table_class: ClassVar[type[tables.Table] | None] = None
    fields: ClassVar[tuple[TableField | str, ...] | str | None] = None
    exclude: ClassVar[tuple[str, ...] | str | None] = None

    # ------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------

    show_search = True
    search_fields: ClassVar[tuple[str, ...]] = ()
    search_parameter = "q"

    # ------------------------------------------------------------------
    # FILTERING
    # ------------------------------------------------------------------

    show_filters = True
    filterset_class: ClassVar[type[django_filters.FilterSet] | None] = None

    # ------------------------------------------------------------------
    # ALPHABET FILTER
    # ------------------------------------------------------------------

    show_alphabet_filter = True
    alphabet: ClassVar[tuple[str, ...]] = tuple(ascii_uppercase)
    alphabet_parameter = "letter"
    alphabet_field= "name"

    # ------------------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------------------

    paginate = True
    page_size = 20

    page_parameter = "page"
    page_size_parameter = "page_size"

    page_size_options: ClassVar[tuple[int, ...]] = (10, 20, 50, 100)
    max_page_size = 100

    show_pagination = True
    show_page_size = True

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    actions: ClassVar[Actions] = Actions()
    row_actions: ClassVar[Actions] = Actions()
    bulk_actions: ClassVar[Actions] = Actions()

    context_menu = True

    # ------------------------------------------------------------------
    # SELECTION
    # ------------------------------------------------------------------

    selectable = True
    objects_parameter = "objects"

    # ------------------------------------------------------------------
    # DISPLAY
    # ------------------------------------------------------------------

    show_header = True
    show_footer = True
    empty_message = "No records found."

    # ------------------------------------------------------------------
    # LIFECYCLE
    # ------------------------------------------------------------------

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initialize(self) -> None:
        super().initialize()

        self.table: tables.Table | None = None
        self.filterset = None

        self.search = SearchComposer(
            request=self.request,
            fields=self.search_fields,
            parameter=self.search_parameter,
        )

        self.filters = FilterComposer(
            request=self.request,
            filterset_class=(
                self.filterset_class
                if self.show_filters
                else None
            ),
        )

        self.table_composer = TableComposer(
            request=self.request,
            model=self.model,
            table_class=self.table_class,
            fields=self.fields,
            exclude=self.exclude,
            row_actions=bool(self.row_actions),
            paginate=self.paginate,
            page_size=self.page_size,
            page_parameter=self.page_parameter,
            page_size_parameter=self.page_size_parameter,
            page_size_options=self.page_size_options,
            max_page_size=self.max_page_size,
        )

        self.page_size_options = tuple(sorted(set(self.page_size_options) | {self.page_size}))

    def configure(self) -> None:
        super().configure()
        self.table = self.build_table()

    # ------------------------------------------------------------------
    # QUERYSET
    # ------------------------------------------------------------------

    def get_queryset(self):
        queryset = super().get_queryset()

        queryset = self.filters.apply(queryset)
        self.filterset = self.filters.filterset

        if self.show_search:
            queryset = self.search.apply(queryset)

        return self.apply_alphabet_filter(queryset)

    def apply_alphabet_filter(self, queryset):
        if not self.show_alphabet_filter or not self.alphabet_field:
            return queryset

        letter = self.get_current_letter()

        if letter not in self.alphabet:
            return queryset

        return queryset.filter(
            **{
                f"{self.alphabet_field}__istartswith": letter,
            }
        )

    def get_current_letter(self) -> str | None:
        letter = self.query_state.get(self.alphabet_parameter)

        return str(letter).upper() if letter else None

    # ------------------------------------------------------------------
    # TABLE
    # ------------------------------------------------------------------

    def build_table(self) -> tables.Table:
        table = self.table_composer.compose(self.get_queryset())

        # Used by RowActionsColumn to resolve row-specific actions.
        table.widget = self

        return table

    # ------------------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------------------

    def get_page_size(self) -> int:
        return self.table_composer.pagination.get_page_size()

    def get_page_size_options(self) -> tuple[int, ...]:
        return tuple(
            size
            for size in self.page_size_options
            if 0 < size <= self.max_page_size
        )

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    def compose_actions(
        self,
        actions: Actions,
        *,
        obj: Any = None,
        objects: Any = None,
    ):
        return ActionComposer(
            widget=self,
            request=self.request,
            actions=actions,
            object=obj,
            objects=objects,
            data=self.get_data(),
        ).compose()

    def get_table_actions(self):
        return self.compose_actions(self.actions)

    def get_row_actions(self, obj: Any):
        return self.compose_actions(
            self.row_actions,
            obj=obj,
            objects=(obj,),
        )

    def get_bulk_actions(self):
        return self.compose_actions(
            self.bulk_actions,
            objects=self.get_objects(),
        )

    def get_context_menu_actions(self):
        if not self.context_menu:
            return Actions()

        return self.row_actions

    @property
    def table_target(self):
        return f"#{self.id}"

    # ------------------------------------------------------------------
    # CONTEXT
    # ------------------------------------------------------------------

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()

        context.update(
            {
                "title": getattr(self, "title", ""),
                "description": getattr(self, "description", ""),

                # Table
                "table": self.table,
                "table_id": self.id,
                "table_url": self.base_url,
                "table_target": self.table_target,
                "empty_message": self.empty_message,

                # Search
                "show_search": self.show_search,
                "search_parameter": self.search_parameter,
                "search_term": self.query_state.get(self.search_parameter),

                # Filters
                "show_filters": self.show_filters,
                "filterset": self.filterset,

                # Alphabet
                "show_alphabet_filter": (
                    self.show_alphabet_filter
                    and bool(self.alphabet_field)
                ),
                "alphabet": self.alphabet,
                "alphabet_parameter": self.alphabet_parameter,
                "current_letter": self.get_current_letter(),

                # Pagination
                "show_pagination": self.show_pagination and self.paginate,
                "show_page_size": self.show_page_size and self.paginate,
                "page_size": self.get_page_size(),
                # Display

                "page_parameter": self.page_parameter,
                "page_size_options": self.get_page_size_options(),
                "page_size_parameter": self.page_size_parameter,

                # Actions
                "table_actions": self.get_table_actions(),
                "bulk_actions": self.get_bulk_actions(),

                # Selection
                "selectable": self.selectable,
                "objects_parameter": self.objects_parameter,

                # Display
                "show_header": self.show_header,
                "show_footer": self.show_footer,

                # Context menu
                "context_menu_enabled": (
                    self.context_menu
                    and bool(self.row_actions)
                ),
                "context_menu_actions": self.get_context_menu_actions(),
            }
        )

        return context
