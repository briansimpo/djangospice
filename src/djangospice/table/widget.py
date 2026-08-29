from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

import django_tables2 as tables
from django.db.models import Q, QuerySet

from djangospice.table.columns import RowActionsColumn
from djangospice.widgets.actions import (
    Action,
    ActionCollection,
    ActionContext,
    BoundAction,
)
from djangospice.widgets.widget import Widget

from .metaclass import TableWidgetMetaclass
from .page import PageContext


class TableWidget(Widget, metaclass=TableWidgetMetaclass):
    """
    Production-ready django-tables2 based widget.

    django-tables2 owns:

        - columns
        - table rendering
        - ordering
        - pagination

    TableWidget owns:

        - queryset preparation
        - search
        - django-filter integration
        - actions
        - HTMX navigation
        - selection state
    """

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------

    table_class: ClassVar[type[tables.Table] | None] = None

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    table_actions: ClassVar[ActionCollection]
    row_actions: ClassVar[ActionCollection]
    bulk_actions: ClassVar[ActionCollection]

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    search_fields: ClassVar[tuple[str, ...]] = ()
    search_parameter: ClassVar[str] = "search"

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    filterset_class: ClassVar[Any | None] = None

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    per_page: ClassVar[int] = 25

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    empty_message: ClassVar[str] = "No records found."

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------

    table: tables.Table
    filterset: Any | None

    # ==================================================================
    # Lifecycle
    # ==================================================================

    def initialize(self) -> None:
        self.filterset = None

    def configure(self) -> None:
        self.table = self.build_table()

    # ==================================================================
    # Queryset
    # ==================================================================

    def get_table_queryset(self) -> QuerySet:
        queryset = self.get_queryset()
        queryset = self.apply_filters(queryset)
        queryset = self.apply_search(queryset)

        return queryset

    # ==================================================================
    # Filters
    # ==================================================================

    def get_filterset_class(self):
        return self.filterset_class

    def get_filterset(self, queryset: QuerySet):
        filterset_class = self.get_filterset_class()

        if filterset_class is None:
            return None

        return filterset_class(
            data=self.request.GET if self.request else None,
            queryset=queryset,
            request=self.request,
        )

    def apply_filters(self, queryset: QuerySet) -> QuerySet:
        self.filterset = self.get_filterset(queryset)

        if self.filterset is None:
            return queryset

        return self.filterset.qs

    # ==================================================================
    # Search
    # ==================================================================

    def get_search_term(self) -> str:
        if self.request is None:
            return ""

        return self.request.GET.get(
            self.search_parameter,
            "",
        ).strip()

    def apply_search(self, queryset: QuerySet) -> QuerySet:
        term = self.get_search_term()

        if not term or not self.search_fields:
            return queryset

        query = Q()

        for field in self.search_fields:
            query |= Q(
                **{
                    f"{field}__icontains": term,
                }
            )

        return queryset.filter(query)

    # ==================================================================
    # django-tables2
    # ==================================================================

    def get_table_class(self):
        table_class = self._meta.table_class

        if not self.row_actions:
            return table_class

        return type(
            f"{table_class.__name__}WidgetTable",
            (table_class,),
            {
                "row_actions": RowActionsColumn(
                    verbose_name="",
                    orderable=False,
                ),
            },
        )
   
    def build_table(self) -> tables.Table:
        queryset = self.get_table_queryset()

        table_class = self.get_table_class()

        table = table_class(queryset, request=self.request)

        # Give custom columns access to the widget.
        table.widget = self

        tables.RequestConfig(
            self.request,
            paginate={"per_page": self.per_page},
        ).configure(table)

        return table

    def get_page_context(self) -> PageContext:
        page = self.table.page
        paginator = self.table.paginator

        navigation = self.navigation

        return PageContext(
            number=page.number,
            total=paginator.num_pages,
            has_previous=page.has_previous(),
            has_next=page.has_next(),

            previous=(
                navigation.page(
                    page.previous_page_number(),
                )
                if page.has_previous()
                else None
            ),

            next=(
                navigation.page(
                    page.next_page_number(),
                )
                if page.has_next()
                else None
            ),

            first=(
                navigation.page(1)
                if page.number > 1
                else None
            ),

            last=(
                navigation.page(
                    paginator.num_pages,
                )
                if page.number < paginator.num_pages
                else None
            ),

            pages=tuple(
                (
                    number,
                    navigation.page(number),
                    number == page.number,
                )
                for number in paginator.page_range
            ),
        )

    # ==================================================================
    # Actions
    # ==================================================================

    def get_table_action_context(self) -> ActionContext:
        return ActionContext(
            widget=self,
            request=self.request,
            data=self.get_data(),
        )

    def get_row_action_context(self, obj: Any) -> ActionContext:

        return ActionContext(
            widget=self,
            request=self.request,
            object=obj,
            objects=(obj,),
            data=self.get_data(),
        )

    def get_bulk_action_context(self) -> ActionContext:
        return ActionContext(
            widget=self,
            request=self.request,
            objects=self.get_objects(),
            data=self.get_data(),
        )

    @staticmethod
    def bind_action(action: Action, context: ActionContext) -> BoundAction:

        return BoundAction(
            action=action,
            context=context,
        )

    def get_table_actions(self) -> tuple[BoundAction, ...]:
        context = self.get_table_action_context()

        return tuple(
            self.bind_action(action, context)
            for action in self.table_actions
            if action.visible(context)
        )

    def get_row_actions(self, obj: Any) -> tuple[BoundAction, ...]:

        context = self.get_row_action_context(obj)

        return tuple(
            self.bind_action(action, context)
            for action in self.row_actions
            if action.visible(context)
        )

    def get_bulk_actions(self) -> tuple[BoundAction, ...]:
        context = self.get_bulk_action_context()

        return tuple(
            self.bind_action(action, context)
            for action in self.bulk_actions
            if action.visible(context)
        )

    # ==================================================================
    # IDs
    # ==================================================================

    @property
    def table_id(self) -> str:
        return f"{self.name}-table"

    @property
    def content_id(self) -> str:
        return f"{self.name}-content"

    @property
    def selection_id(self) -> str:
        return f"{self.name}-selection"

    @property
    def htmx_target(self) -> str:
        return f"#{self.content_id}"

    # ==================================================================
    # Context
    # ==================================================================

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()

        context.update(
            table=self.table,
            filterset=self.filterset,

            search_term=self.get_search_term(),
            search_parameter=self.search_parameter,
            search_enabled=bool(self.search_fields),

            table_actions=self.get_table_actions(),
            bulk_actions=self.get_bulk_actions(),

            table_id=self.table_id,
            content_id=self.content_id,
            selection_id=self.selection_id,

            table_url=self.endpoint,
            navigation=self.navigation,
            page=self.get_page_context(),

            empty_message=self.empty_message,
            htmx_target=self.htmx_target,
        )

        return context
