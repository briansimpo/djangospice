from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, fields
from typing import Any, Mapping

import django_filters
import django_tables2 as tables


@dataclass
class TableOptions:
    """
    Declarative configuration for TableWidget.

    Resolution order:

        inherited options
            ↓
        Meta
            ↓
        class attributes

    The resulting TableOptions is the single runtime source
    of truth for table-specific configuration.
    """

    table_class: type[tables.Table] | None = None

    fields: tuple[str, ...] | str | None = None
    exclude: tuple[str, ...] | str | None = None

    columns: Mapping[str, tables.Column] = field(
        default_factory=dict
    )

    table_options: dict[str, Any] = field(
        default_factory=dict
    )

    # Search ------------------------------------------------------------

    search_fields: tuple[str, ...] = ()
    search_parameter: str = "q"

    # Filtering ---------------------------------------------------------

    filterset_class: type[django_filters.FilterSet] | None = None

    # Pagination --------------------------------------------------------

    paginate: bool = True
    paginate_by: int = 25
    max_page_size: int = 100

    page_parameter: str = "page"
    page_size_parameter: str = "page_size"

    # Selection ---------------------------------------------------------

    selectable: bool = False
    selection_parameter: str = "selected_ids"

    # UI ----------------------------------------------------------------

    toolbar: bool = True
    show_search: bool = True
    show_filters: bool = True

    @classmethod
    def from_declaration(
        cls,
        *,
        bases: tuple[type, ...],
        meta: type | None,
        attrs: dict[str, Any],
    ) -> "TableOptions":

        values: dict[str, Any] = {}

        option_fields = {
            field.name
            for field in fields(cls)
        }

        # --------------------------------------------------------------
        # 1. Inherited configuration
        # --------------------------------------------------------------

        for base in bases:

            parent = getattr(
                base,
                "_table_options",
                None,
            )

            if parent is None:
                continue

            for field_name in option_fields:
                if hasattr(parent, field_name):
                    values[field_name] = deepcopy(
                        getattr(parent, field_name)
                    )

        # --------------------------------------------------------------
        # 2. Meta configuration
        # --------------------------------------------------------------

        if meta is not None:

            for field_name in option_fields:

                if hasattr(meta, field_name):
                    values[field_name] = getattr(
                        meta,
                        field_name,
                    )

        # --------------------------------------------------------------
        # 3. Explicit class attributes
        # --------------------------------------------------------------

        for field_name in option_fields:

            if field_name in attrs:
                values[field_name] = attrs[field_name]

        return cls(**values)