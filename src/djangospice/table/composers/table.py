from __future__ import annotations

from typing import Any

import django_tables2 as tables

from djangospice.table.columns import RowActionsColumn
from djangospice.table.fields import Field

from .page import TablePaginationComposer


class TableComposer:
    """Builds and configures a django-tables2 table."""

    def __init__(self, widget: Any) -> None:
        self.widget = widget

    def get_fields(self) -> tuple[Field, ...] | None:
        """Normalize string and Field declarations."""

        fields = self.widget.fields

        if fields is None:
            return None

        if isinstance(fields, (str, Field)):
            fields = (fields,)

        return tuple(
            Field.normalize(item)
            for item in fields
        )

    def get_class(self) -> type[tables.Table]:
        widget = self.widget

        if widget.table_class is not None:
            table_class = widget.table_class
        else:
            if widget.model is None:
                raise ValueError(
                    f"{widget.__class__.__name__} requires either "
                    "'table_class' or 'model'."
                )

            fields = self.get_fields()

            if fields is None:
                table_class = tables.table_factory(
                    widget.model,
                    exclude=widget.exclude,
                )
            else:
                included_fields = tuple(
                    item
                    for item in fields
                    if not item.exclude
                )

                field_names = tuple(
                    item.name
                    for item in included_fields
                )

                table_class = tables.table_factory(
                    widget.model,
                    fields=field_names,
                    exclude=widget.exclude,
                )

                # Replace generated columns with configured Field columns.
                custom_columns = {
                    item.name: tables.Column(
                        accessor=item.accessor,
                        verbose_name=item.label,
                        orderable=item.sortable,
                        visible=item.visible,
                        attrs=item.attrs,
                    )
                    for item in included_fields
                    if isinstance(item, Field)
                }

                if custom_columns:
                    table_class = type(
                        f"{table_class.__name__}Configured",
                        (table_class,),
                        custom_columns,
                    )

        if not widget.row_actions:
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

    def compose(self, queryset) -> tables.Table:
        widget = self.widget

        table = self.get_class()(
            queryset,
            request=widget.request,
        )

        table.widget = widget

        TablePaginationComposer(
            request=widget.request,
            config=widget.pagination_config,
        ).configure(table)

        return table