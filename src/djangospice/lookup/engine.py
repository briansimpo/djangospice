from __future__ import annotations

from typing import Any

from django.core.paginator import Paginator
from django.db.models import Q, QuerySet

from .query import LookupQuery
from .result import LookupOption, LookupResult
from .search import get_search_fields
from .resolver import RelationResolver


class LookupEngine:

    def execute(self, query: LookupQuery) -> LookupResult:

        queryset = self.get_queryset(
            query.model
        )

        queryset = self.apply_filters(
            queryset,
            query.filters,
        )

        queryset = self.apply_search(
            queryset,
            query.search,
        )

        queryset = self.order_queryset(
            queryset,
        )

        paginator = Paginator(
            queryset,
            query.normalized_page_size,
        )

        page = paginator.get_page(
            query.normalized_page,
        )

        return LookupResult(
            options=tuple(
                self.to_option(obj)
                for obj in page.object_list
            ),
            page=page.number,
            page_size=query.normalized_page_size,
            total=paginator.count,
            has_next=page.has_next(),
            has_previous=page.has_previous(),
        )

    def get_queryset(self, model) -> QuerySet:

        return model._default_manager.all()

    def apply_filters(self, queryset: QuerySet, filters: dict[str, Any]) -> QuerySet:

        for path, value in filters.items():

            fields = RelationResolver.resolve(
                queryset.model,
                path,
            )

            if value in (None, ""):
                continue

            lookup = self.build_relation_lookup(
                fields,
                path,
                value,
            )

            queryset = queryset.filter(
                **lookup
            )

        return queryset

    def build_relation_lookup(self, fields, path: str, value: Any) -> dict[str, Any]:

        final_field = fields[-1]

        if final_field.many_to_many:
            return {
                path: value,
            }

        if final_field.many_to_one:
            return {
                f"{path}__pk": value,
            }

        if final_field.one_to_one:
            return {
                f"{path}__pk": value,
            }

        raise ValueError(
            f"Unsupported relationship type "
            f"for lookup '{path}'."
        )

    def apply_search(self, queryset: QuerySet, search: str) -> QuerySet:

        search = search.strip()

        if not search:
            return queryset

        fields = get_search_fields(
            queryset.model
        )

        if not fields:
            return queryset.none()

        condition = Q()

        for field in fields:
            condition |= Q(
                **{
                    f"{field}__icontains": search,
                }
            )

        return queryset.filter(condition)

    def order_queryset(self, queryset: QuerySet) -> QuerySet:

        fields = get_search_fields(
            queryset.model
        )

        if "code" in fields:
            return queryset.order_by(
                "code"
            )

        if "name" in fields:
            return queryset.order_by(
                "name"
            )

        if "title" in fields:
            return queryset.order_by(
                "title"
            )

        return queryset.order_by(
            queryset.model._meta.pk.name
        )

    def to_option(self, obj) -> LookupOption:

        return LookupOption(
            value=str(obj.pk),
            label=str(obj),
        )