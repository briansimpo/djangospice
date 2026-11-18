
from __future__ import annotations

from string import ascii_uppercase
from typing import Any, ClassVar

import django_filters
import django_tables2 as tables

from djangospice.exec.action import Actions
from djangospice.exec.decorators import get
from djangospice.table.job import TableExportJob
from djangospice.utils import get_template_name
from djangospice.widget.widget import Widget

from .composers import TableComposer, FilterComposer, SearchComposer
from .fields import TableField
from .skeleton import TableSkeleton
from .apps import namespace


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

    searchable = True
    search_fields: ClassVar[tuple[str, ...]] = ()
    search_parameter = "q"

    # ------------------------------------------------------------------
    # FILTERING
    # ------------------------------------------------------------------

    filterable = True
    filterset_class: ClassVar[type[django_filters.FilterSet] | None] = None

    # ------------------------------------------------------------------
    # ALPHABET FILTER
    # ------------------------------------------------------------------

    show_alphabet = True
    alphabet: ClassVar[tuple[str, ...]] = tuple(ascii_uppercase)
    alphabet_parameter = "letter"
    alphabet_field = "name"

    # ------------------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------------------

    paginate = True
    sortable = True
    page_size = 20
    page_parameter = "page"
    page_size_parameter = "page_size"
    page_size_options: ClassVar[tuple[int, ...]] = (10, 20, 50, 100)
    max_page_size = 100

    # ------------------------------------------------------------------
    # SELECTION
    # ------------------------------------------------------------------

    selectable = True
    object_parameter = "id"
    objects_parameter = "ids"

    # ------------------------------------------------------------------
    # DISPLAY
    # ------------------------------------------------------------------

    show_header = True
    show_footer = True
    empty_message = "No records found."

    row_url = None
    row_target = "_self"

    # ------------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------------

    exportable = True

    export_formats: ClassVar[tuple[str, ...]] = (
        "csv",
        "xlsx",
    )

    export_directory = "exports"
    export_unique_filename = True

    # ------------------------------------------------------------------
    # LIFECYCLE
    # ------------------------------------------------------------------

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
                self.filterset_class if self.filterable else None
            ),
        )

        self.table_composer = TableComposer(
            request=self.request,
            model=self.model,
            table_class=self.table_class,
            fields=self.fields,
            exclude=self.exclude,
            paginate=self.paginate,
            page_size=self.page_size,
            page_parameter=self.page_parameter,
            page_size_parameter=self.page_size_parameter,
            page_size_options=self.page_size_options,
            max_page_size=self.max_page_size,
        )

        self.page_size_options = tuple(
            sorted(set(self.page_size_options) | {self.page_size})
        )

    def configure(self) -> None:
        super().configure()
        self.table = self.build_table()

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    @property
    def row_actions(self) -> Actions:
        return self.get_actions_by_group("row")

    @property
    def bulk_actions(self) -> Actions:
        return self.get_actions_by_group("bulk")

    # ------------------------------------------------------------------
    # SELECTION
    # ------------------------------------------------------------------

    def get_selected_rows(self):
        if not self.request:
            return []

        return self.get_list(self.objects_parameter)

    def get_selected_row(self):
        if not self.request:
            return None

        return self.get_value(self.object_parameter)

    # ------------------------------------------------------------------
    # DISPLAY
    # ------------------------------------------------------------------

    def get_row_url(self):
        return self.row_url

    def get_row_target(self):
        return self.row_target

    def get_skeleton(self):
        return TableSkeleton(rows=10)

    # ------------------------------------------------------------------
    # QUERYSET
    # ------------------------------------------------------------------

    def get_queryset(self):
        """
        Build the queryset using the current request state.

        Filtering order:
        1. Base queryset
        2. FilterSet
        3. Search
        4. Alphabet filter
        """
        queryset = super().get_queryset()

        queryset = self.filters.apply(queryset)
        self.filterset = self.filters.filterset

        if self.searchable:
            queryset = self.search.apply(queryset)

        return self.apply_alphabet_filter(queryset)

    def apply_alphabet_filter(self, queryset):
        if not self.show_alphabet or not self.alphabet_field:
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
                "table_target": self.get_widget_target(),
                "empty_message": self.empty_message,

                # Search
                "searchable": self.searchable,
                "sortable": self.sortable,
                "search_parameter": self.search_parameter,
                "search_term": self.query_state.get(
                    self.search_parameter
                ),

                # Filters
                "filterable": self.filterable,
                "filterset": self.filterset,

                # Alphabet
                "show_alphabet": self.show_alphabet,
                "alphabet": self.alphabet,
                "alphabet_parameter": self.alphabet_parameter,
                "current_letter": self.get_current_letter(),

                # Pagination
                "page_size": self.get_page_size(),
                "page_parameter": self.page_parameter,
                "page_size_options": self.get_page_size_options(),
                "page_size_parameter": self.page_size_parameter,

                # Actions
                "bulk_actions": self.bulk_actions,
                "row_actions": self.row_actions,

                # Selection
                "selectable": self.selectable,
                "object_parameter": self.object_parameter,
                "objects_parameter": self.objects_parameter,

                # Display
                "show_header": self.show_header,
                "show_footer": self.show_footer,

                "row_url": self.get_row_url(),
                "row_target": self.get_row_target(),

                # Export
                "exportable": self.exportable,
                "export_formats": self.export_formats,
            }
        )

        return context

    # ------------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------------

    
    def get_export_configuration(self) -> tuple[type, type]:
        """Resolve the table and model classes."""
        return self.table_composer.resolve()

    def get_export_filters(self) -> dict:
        filters = {}

        # FilterSet filters
        if self.filterable and self.filterset:
            form = self.filterset.form

            if form.is_valid():
                for name, value in form.cleaned_data.items():
                    if value in (None, "", [], (), {}):
                        continue

                    filter_field = self.filterset.filters[name]

                    if filter_field.method:
                        raise ValueError(
                            f"Custom filter method '{name}' requires "
                            "an explicit export implementation."
                        )

                    field_name = filter_field.field_name
                    lookup_expr = filter_field.lookup_expr

                    if lookup_expr != "exact":
                        field_name = f"{field_name}__{lookup_expr}"

                    if hasattr(value, "pk"):
                        value = value.pk
                    elif hasattr(value, "values_list"):
                        value = list(value.values_list("pk", flat=True))

                    filters[field_name] = value

        # Search
        search = None

        if self.searchable and self.search_fields:
            search_term = self.query_state.get(self.search_parameter)

            if search_term:
                search = {
                    "fields": list(self.search_fields),
                    "value": search_term,
                }

        # Alphabet
        alphabet = None

        if self.show_alphabet:
            letter = self.query_state.get(self.alphabet_parameter)

            if letter and letter.upper() in self.alphabet:
                alphabet = {
                    "field": self.alphabet_field,
                    "value": letter.upper(),
                }

        return {
            "filters": filters,
            "search": search,
            "alphabet": alphabet,
        }

    def export_data(self, export_format: str):
        if not self.exportable:
            return self.response().error("Export is disabled.")

        export_format = export_format.lower().lstrip(".")

        if export_format not in self.export_formats:
            return self.response().error(
                f"Unsupported export format: {export_format}"
            )

        table_class, model_class = self.get_export_configuration()

        job = TableExportJob.create(
            table_class=table_class,
            model_class=model_class,
            export_format=export_format,
            filters=self.get_export_filters(),
            directory=self.export_directory,
            rename_file=self.export_unique_filename,
        )

        job_result = job.dispatch_now()
        file_path, file_url = job_result.result
        return self.response().redirect(file_url).success("Data Export completed successfully")

    @get
    def export_excel(self):
        return self.export_data("xlsx")

    @get
    def export_csv(self):
        return self.export_data("csv")
