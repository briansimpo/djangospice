
from __future__ import annotations
from typing import Any, Iterable

import django_tables2 as tables
import django_filters

from django_filters.filterset import filterset_factory
from django.db.models import Q, QuerySet
from djangospice.filters.filter import DynamicFilter

from .fields import TableField
from .resolver import TableResolver


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


class FilterComposer:
    """
    Integrates django-filter into a queryset pipeline.

    Supports:
    - Custom FilterSet classes.
    - Automatically generated FilterSets from model fields.
    """

    def __init__(
        self,
        *,
        request=None,
        model=None,
        filter_class: type[django_filters.FilterSet] | None = None,
        filter_fields: tuple[str, ...] | dict | None = None,
    ) -> None:
        self.request = request
        self.model = model
        self.filter_class = filter_class
        self.filter_fields = filter_fields

        self.filterset: django_filters.FilterSet | None = None

    def get_filter_class(self):
        if self.filter_class is not None:
            return self.filter_class

        if self.filter_fields is None or self.model is None:
            return None

        return filterset_factory(
            model=self.model,
            fields=self.filter_fields,
            filterset=DynamicFilter
        )

    def compose(self, queryset: QuerySet[Any]) -> django_filters.FilterSet | None:

        filter_class = self.get_filter_class()

        if filter_class is None:
            self.filterset = None
            return None

        self.filterset = filter_class(
            data=self.request.GET if self.request else None,
            queryset=queryset,
            request=self.request,
        )

        return self.filterset

    def apply(self, queryset: QuerySet[Any]) -> QuerySet[Any]:
        filterset = self.compose(queryset)

        if filterset is None:
            return queryset

        return filterset.qs


class SearchComposer:
    """
    Applies OR-based icontains search across configured fields.
    """

    def __init__(
        self,
        *,
        request=None,
        fields: Iterable[str] = (),
        parameter: str = "q",
    ) -> None:
        self.request = request
        self.fields = tuple(fields)
        self.parameter = parameter

    def get_term(self) -> str:
        if self.request is None:
            return ""

        return self.request.GET.get(self.parameter, "").strip()

    def apply(self, queryset: QuerySet[Any]) -> QuerySet[Any]:
        term = self.get_term()

        if not term or not self.fields:
            return queryset

        query = Q()

        for field in self.fields:
            query |= Q(**{f"{field}__icontains": term})

        return queryset.filter(query)


class TableComposer:

    def __init__(
        self,
        *,
        request: Any,
        model: type | None = None,
        table_class: type[tables.Table] | None = None,
        fields: Iterable[TableField | str] | str | TableField | None = None,
        exclude: Iterable[str] | str | None = None,
        paginate: bool = True,
        page_size: int = 20,
        page_parameter: str = "page",
        page_size_parameter: str = "page_size",
        page_size_options: Iterable[int] = (10, 20, 50, 100),
        max_page_size: int = 100,
    ):
        self.request = request

        self.resolver = TableResolver(
            model=model,
            table_class=table_class,
            fields=fields,
            exclude=exclude,
        )

        self.pagination = PaginationComposer(
            request=request,
            enabled=paginate,
            page_size=page_size,
            page_parameter=page_parameter,
            page_size_parameter=page_size_parameter,
            page_size_options=page_size_options,
            max_page_size=max_page_size,
        )

    def compose(self, queryset):
        table_class, _ = self.resolver.resolve()

        table = table_class(
            queryset,
            request=self.request,
        )

        return self.pagination.configure(table)