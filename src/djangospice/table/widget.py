from __future__ import annotations

from typing import Any, ClassVar

import django_filters
import django_tables2 as tables

from djangospice.templates import get_template_name
from djangospice.widget.widget import Widget
from djangospice.widget.actions import Actions
from djangospice.widget.pagination import (
    PaginationConfig,
    PaginationState
)
from djangospice.widget.composers import (
    ActionComposer,
    FilterComposer,
    PaginationComposer,
    SearchComposer,
)

from .composers import TableComposer, TablePageComposer
from .fields import Field
from .apps import namespace



class Table(Widget):
    """
    Request-aware server-side table widget built on django-tables2.

    The widget composes generic queryset, filtering, search, pagination,
    and action services with table-specific django-tables2 behavior.
    """

    template_name = get_template_name("table.html", namespace)

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------

    table_class: ClassVar[type[tables.Table] | None] = None
    fields: ClassVar[tuple[Field | str, ...] | str | None] = None
    exclude: ClassVar[tuple[str, ...] | str | None] = None

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    actions: ClassVar[Actions] = Actions()
    row_actions: ClassVar[Actions] = Actions()
    bulk_actions: ClassVar[Actions] = Actions()

    context_menu: ClassVar[bool] = True
    context_menu_actions: ClassVar[Actions | None] = None

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    search_fields: ClassVar[tuple[str, ...]] = ()
    search_parameter: ClassVar[str] = "q"

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    filterset_class: ClassVar[
        type[django_filters.FilterSet] | None
    ] = None

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    page_size_options: ClassVar[tuple[int, ...]] = (
        10,
        20,
        50,
        100,
        500,
    )

    paginate: ClassVar[bool] = True
    paginate_by: ClassVar[int] = 20
    max_page_size: ClassVar[int] = 100

    page_parameter: ClassVar[str] = "page"
    page_size_parameter: ClassVar[str] = "page_size"

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    selectable: ClassVar[bool] = False

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    toolbar: ClassVar[bool] = True
    show_search: ClassVar[bool] = True
    show_filters: ClassVar[bool] = True

    show_header: ClassVar[bool] = True
    show_footer: ClassVar[bool] = True

    empty_message: ClassVar[str] = "No records found."

    # ------------------------------------------------------------------
    # Runtime state
    # ------------------------------------------------------------------

    table: tables.Table
    filterset: django_filters.FilterSet | None
    pagination_config: PaginationConfig
    pagination_state: PaginationState

    alphabet_parameter: ClassVar[str] = "letter"
    alphabet_field: ClassVar[str | None] = None

    # ==================================================================
    # Lifecycle
    # ==================================================================

    def initialize(self) -> None:
        super().initialize()

        self.filterset = None
        self.pagination_state = None

        self.search = SearchComposer(
            request=self.request,
            fields=self.search_fields,
            parameter=self.search_parameter,
        )

        self.filters = FilterComposer(
            request=self.request,
            filterset_class=self.filterset_class,
        )

        self.pagination = PaginationComposer(
            request=self.request,
            paginate=self.paginate,
            default_size=self.paginate_by,
            size_options=self.page_size_options,
            max_size=self.max_page_size,
            page_parameter=self.page_parameter,
            size_parameter=self.page_size_parameter,
        )

        self.pagination_config = self.pagination.compose()

        self.table_composer = TableComposer(self)

    def configure(self) -> None:
        super().configure()

        self.table = self.build_table()

        self.pagination_state = TablePageComposer(
            table=self.table,
            config=self.pagination_config,
        ).compose()

    def get_alphabet_options(self) -> list[str]:
        """Returns uppercase letters A through Z."""
        import string
        return list(string.ascii_uppercase)

    def get_current_letter(self) -> str | None:
        """Retrieves the currently selected letter from QueryState or request."""
        return self.query_state.get(self.alphabet_parameter)


    # ==================================================================
    # Queryset
    # ==================================================================
    def get_table_queryset(self):
        queryset = self.get_queryset()
        queryset = self.apply_filters(queryset)
        queryset = self.search.apply(queryset)
        
        # Apply alphabet filtering if configured
        letter = self.get_current_letter()
        if letter and self.alphabet_field:
            filter_kwargs = {f"{self.alphabet_field}__startswith": letter}
            queryset = queryset.filter(**filter_kwargs)
            
        return queryset

    def apply_filters(self, queryset):
        queryset = self.filters.apply(queryset)
        self.filterset = self.filters.filterset
        return queryset

    # ==================================================================
    # Table
    # ==================================================================

    def get_table_class(self) -> type[tables.Table]:
        return self.table_composer.get_class()

    def build_table(self) -> tables.Table:
        queryset = self.get_table_queryset()

        return self.table_composer.compose(queryset)

    # ==================================================================
    # Pagination
    # ==================================================================

    def get_page_size_options(self) -> tuple[int, ...]:
        return self.pagination_config.page_size_options

    def get_page_size(self) -> int:
        return self.pagination_config.page_size

    def get_page(self):
        return self.pagination_state

    # ==================================================================
    # Actions
    # ==================================================================

    def get_table_actions(self):
        return ActionComposer(
            widget=self,
            request=self.request,
            actions=self.actions,
            data=self.get_data(),
        ).compose()

    def get_row_actions(self, obj):
        return ActionComposer(
            widget=self,
            request=self.request,
            actions=self.row_actions,
            object=obj,
            objects=(obj,),
            data=self.get_data(),
        ).compose()

    def get_bulk_actions(self):
        return ActionComposer(
            widget=self,
            request=self.request,
            actions=self.bulk_actions,
            objects=self.get_objects(),
            data=self.get_data(),
        ).compose()

    def get_context_menu_actions(self):
        return (
            self.context_menu_actions
            or self.row_actions
        )

    def get_row_context_actions(self, obj):
        return self.get_row_actions(obj)

    # ==================================================================
    # IDs
    # ==================================================================

    @property
    def table_id(self) -> str:
        return f"{self.name}-table"

    @property
    def table_wrapper_id(self) -> str:
        return f"{self.name}-wrapper"

    @property
    def selection_id(self) -> str:
        return f"{self.name}-selection"

    @property
    def htmx_target(self) -> str:
        return f"#{self.table_wrapper_id}"

    @property
    def htmx_indicator(self) -> str:
        return f"{self.name}-loader"

    @property
    def context_menu_id(self) -> str:
        return f"{self.name}-contextmenu"

    @property
    def page_size_id(self) -> str:
        return f"{self.table_id}-pagesize"


    # ==================================================================
    # Context
    # ==================================================================

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()

        context.update(
            table=self.table,
            filterset=self.filterset,

            search_term=self.search.get_term(),
            search_parameter=self.search_parameter,
            search_enabled=bool(self.search_fields),

            table_actions=self.get_table_actions(),
            bulk_actions=self.get_bulk_actions(),

            table_id=self.table_id,
            table_wrapper_id=self.table_wrapper_id,
            selection_id=self.selection_id,

            table_url=self.base_url,

            page=self.pagination_state,

            empty_message=self.empty_message,

            htmx_target=self.htmx_target,
            htmx_indicator=self.htmx_indicator,

            selectable=self.selectable,
            objects_parameter=self.objects_parameter,

            toolbar=self.toolbar,
            show_search=self.show_search,
            show_filters=self.show_filters,

            show_header=self.show_header,
            show_footer=self.show_footer,

            context_menu_enabled=(
                self.context_menu
                and bool(self.get_context_menu_actions())
            ),

            context_menu_id=self.context_menu_id,
            context_menu_actions=self.get_context_menu_actions(),

            page_size=self.get_page_size(),
            page_size_options=self.get_page_size_options(),
            page_size_parameter=self.page_size_parameter,
            page_size_id=self.page_size_id,
            
            alphabet=self.get_alphabet_options(),
            current_letter=self.get_current_letter(),
            alphabet_parameter=self.alphabet_parameter,
        )

        return context