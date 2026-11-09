
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Lookup:
    """
    Configure lookup behavior for a model relationship field.

    Attributes:
        field_name: Model field name.
        placeholder: Select placeholder.
        search_placeholder: Search input placeholder.
        depends_on: Parent field for dependent lookups.
        multi_select: Whether multiple values can be selected.
        options: Additional LookupWidget options.
    """

    field_name: str

    placeholder: str | None = None
    search_placeholder: str | None = None

    depends_on: str | None = None
    multi_select: bool | None = None

    options: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.field_name:
            raise ValueError(
                "Lookup requires a field_name."
            )

        self.options = dict(self.options or {})

    def as_dict(self) -> dict:
        """Return configured widget options."""

        options = dict(self.options)

        explicit_options = {
            "placeholder": self.placeholder,
            "search_placeholder": self.search_placeholder,
            "depends_on": self.depends_on,
            "multi_select": self.multi_select,
        }

        options.update({
            key: value
            for key, value in explicit_options.items()
            if value is not None
        })

        return options
