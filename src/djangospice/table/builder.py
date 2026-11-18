from __future__ import annotations

from typing import Any, Type
from django.db import models
from django.db.models import Q

from djangospice.core.resolver import resolve_class
from djangospice.filters.helpers import dynamic_queryset


class TableBuilder:
    """
    Responsible for class resolution, queryset evaluation, dynamic filtering,
    and compiling the final Django Table instance.
    """

    def __init__(self, table_class: str | Type[Any], model_class: str | Type[models.Model], filters: dict[str, Any] | None = None, table_kwargs: dict[str, Any] | None = None) -> None:
        self.table_class = (
            resolve_class(table_class) if isinstance(table_class, str) else table_class
        )
        self.model_class = (
            resolve_class(model_class) if isinstance(model_class, str) else model_class
        )
        self.filters = filters or {}
        self.table_kwargs = table_kwargs

    def build_queryset(self):
        queryset = self.model_class.objects.all()

        filters = self.filters.get("filters", {})

        if filters:
            queryset = dynamic_queryset(queryset, filters)

        search = self.filters.get("search")

        if search:
            search_query = Q()

            for field in search["fields"]:
                search_query |= Q(
                    **{f"{field}__icontains": search["value"]}
                )

            queryset = queryset.filter(search_query)

        alphabet = self.filters.get("alphabet")

        if alphabet:
            queryset = queryset.filter(
                **{
                    f"{alphabet['field']}__istartswith": alphabet["value"]
                }
            )

        return queryset

    def build_table(self):
        return self.table_class(
            self.build_queryset(),
            **self.table_kwargs,
        )