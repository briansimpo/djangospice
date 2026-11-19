from __future__ import annotations

from django.db.models import Q

from djangospice.core.resolver import resolve_class
from djangospice.filters.helpers import dynamic_queryset
from .resolver import TableResolver


class TableBuilder:

    def __init__(
        self,
        *,
        model=None,
        table_class=None,
        fields=None,
        exclude=None,
        filters=None,
        table_kwargs=None,
    ):
        if isinstance(model, str):
            model = resolve_class(model)

        if isinstance(table_class, str):
            table_class = resolve_class(table_class)

        self.resolver = TableResolver(
            model=model,
            table_class=table_class,
            fields=fields,
            exclude=exclude,
        )

        self.filters = filters or {}
        self.table_kwargs = table_kwargs or {}

    def resolve(self):
        return self.resolver.resolve()

    def build_queryset(self):
        _, model = self.resolve()

        queryset = model.objects.all()

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
                    f"{alphabet['field']}__istartswith":
                    alphabet["value"]
                }
            )

        return queryset

    def build(self):
        table_class, _ = self.resolve()

        return table_class(
            self.build_queryset(),
            **self.table_kwargs,
        )


class TableExportFilter:
    """Build export filters from the active table state."""

    def __init__(
        self,
        *,
        filterset=None,
        query_state=None,
        search_fields=None,
        search_parameter=None,
        alphabet=None,
        alphabet_field=None,
        alphabet_parameter=None,
    ):
        self.filterset = filterset
        self.query_state = query_state
        self.search_fields = search_fields or ()
        self.search_parameter = search_parameter
        self.alphabet = alphabet or ()
        self.alphabet_field = alphabet_field
        self.alphabet_parameter = alphabet_parameter

    def get_filters(self) -> dict:
        filters = {}

        if not self.filterset:
            return filters

        form = self.filterset.form

        if not form.is_valid():
            return filters

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

        return filters

    def get_search(self) -> dict | None:
        if not self.search_fields or not self.search_parameter:
            return None

        search_term = self.query_state.get(self.search_parameter)

        if not search_term:
            return None

        return {
            "fields": list(self.search_fields),
            "value": search_term,
        }

    def get_alphabet(self) -> dict | None:
        if not self.alphabet_parameter or not self.alphabet_field:
            return None

        letter = self.query_state.get(self.alphabet_parameter)

        if not letter or letter.upper() not in self.alphabet:
            return None

        return {
            "field": self.alphabet_field,
            "value": letter.upper(),
        }

    def build(self) -> dict:
        return {
            "filters": self.get_filters(),
            "search": self.get_search(),
            "alphabet": self.get_alphabet(),
        }


class TableExportConfig:
    """Build the serializable table definition for export."""

    def __init__(self, resolver: TableResolver):
        self.resolver = resolver

    def build(self) -> dict:
        _, model_class = self.resolver.resolve()

        return {
            "model_class": model_class,
            "table_class": self.resolver.table_class,
            "table_config": {
                "fields": self.resolver.fields,
                "exclude": self.resolver.exclude,
            },
        }