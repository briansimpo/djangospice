
from __future__ import annotations

from typing import Any, Iterable

import django_tables2 as tables

from djangospice.table.fields import TableField


class PaginationComposer:
    """Configure django-tables2 pagination."""

    def __init__(
        self,
        *,
        request: Any,
        enabled: bool = True,
        page_size: int = 20,
        page_parameter: str = "page",
        page_size_parameter: str = "page_size",
        page_size_options: Iterable[int] = (10, 20, 50, 100),
        max_page_size: int = 100,
    ) -> None:
        self.request = request
        self.enabled = enabled
        self.page_size = page_size
        self.page_parameter = page_parameter
        self.page_size_parameter = page_size_parameter
        self.page_size_options = tuple(
            size
            for size in page_size_options
            if 0 < size <= max_page_size
        )
        self.max_page_size = max_page_size

    def get_page_size(self) -> int:
        """Resolve and validate the requested page size."""

        default = min(self.page_size, self.max_page_size)

        if not self.enabled:
            return default

        requested = self.request.GET.get(self.page_size_parameter)

        if requested is None:
            return default

        try:
            requested = int(requested)
        except (TypeError, ValueError):
            return default

        if requested < 1 or requested > self.max_page_size:
            return default

        if self.page_size_options and requested not in self.page_size_options:
            return default

        return requested

    def configure(self, table: tables.Table) -> tables.Table:
        """Apply pagination to a django-tables2 table."""

        if not self.enabled:
            return table

        return tables.RequestConfig(
            self.request,
            paginate={
                "per_page": self.get_page_size(),
                "page": self.request.GET.get(self.page_parameter),
            },
        ).configure(table)


class TableComposer:
    """Build and configure a django-tables2 table."""

    def __init__(
        self,
        *,
        request: Any,
        model: type | None = None,
        table_class: type[tables.Table] | None = None,
        fields: Iterable[TableField | str] | str | TableField | None = None,
        exclude: Iterable[str] | str | None = None,
        row_actions: bool = False,
        paginate: bool = True,
        paginate_by: int = 20,
        page_parameter: str = "page",
        page_size_parameter: str = "page_size",
        page_size_options: Iterable[int] = (10, 20, 50, 100),
        max_page_size: int = 100,
    ) -> None:
        self.request = request
        self.model = model
        self.table_class = table_class
        self.fields = fields
        self.exclude = exclude
        self.row_actions = row_actions

        self.pagination = PaginationComposer(
            request=request,
            enabled=paginate,
            page_size=paginate_by,
            page_parameter=page_parameter,
            page_size_parameter=page_size_parameter,
            page_size_options=page_size_options,
            max_page_size=max_page_size,
        )

    def get_fields(self) -> tuple[TableField, ...] | None:
        """Normalize field declarations."""

        if self.fields is None:
            return None

        fields = self.fields

        if isinstance(fields, (str, TableField)):
            fields = (fields,)

        return tuple(
            TableField.normalize(item)
            for item in fields
        )

    def get_class(self) -> type[tables.Table]:
        """Resolve the table class and apply configured columns."""

        if self.table_class is not None:
            table_class = self.table_class

        else:
            if self.model is None:
                raise ValueError(
                    "A model or table_class is required to build a table."
                )

            fields = self.get_fields()

            if fields is None:
                table_class = tables.table_factory(
                    self.model,
                    exclude=self.exclude,
                )

            else:
                included_fields = tuple(
                    field
                    for field in fields
                    if not field.exclude
                )

                table_class = tables.table_factory(
                    self.model,
                    fields=tuple(
                        field.name
                        for field in included_fields
                    ),
                    exclude=self.exclude,
                )

                custom_columns = {
                    field.name: tables.Column(
                        accessor=field.accessor,
                        verbose_name=field.label,
                        orderable=field.sortable,
                        visible=field.visible,
                        attrs=field.attrs,
                    )
                    for field in included_fields
                }

                if custom_columns:
                    table_class = type(
                        f"{table_class.__name__}Configured",
                        (table_class,),
                        custom_columns,
                    )

        return table_class

    def compose(self, queryset) -> tables.Table:
        """Build the table and configure pagination."""

        table = self.get_class()(
            queryset,
            request=self.request,
        )

        return self.pagination.configure(table)
