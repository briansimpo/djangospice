from __future__ import annotations

import django_tables2 as tables
from django.db import models
from .fields import TableField


def create_table_class(*, model: type[models.Model], fields=None, exclude=None) -> type[tables.Table]:
    """Create a table class from a model and field configuration."""

    if fields is not None:
        if isinstance(fields, (str, TableField)):
            fields = (fields,)

        fields = tuple(
            TableField.normalize(item)
            for item in fields
        )

        included_fields = tuple(
            field for field in fields
            if not field.exclude
        )

        table_class = tables.table_factory(
            model,
            fields=tuple(field.name for field in included_fields),
            exclude=exclude,
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

    return tables.table_factory(
        model,
        exclude=exclude,
    )