
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django import forms
from django.db import models
from django.forms import BaseInlineFormSet


@dataclass
class Inline:
    relation: str | None = None
    model: type[models.Model] | None = None
    fk_name: str | None = None

    form: type[forms.ModelForm] | None = None
    formset: type[BaseInlineFormSet] = BaseInlineFormSet

    fields: Any = "__all__"
    exclude: Any = None

    extra: int | None = None
    can_delete: bool = True
    can_delete_extra: bool = True

    min_num: int | None = None
    max_num: int | None = None

    validate_min: bool = False
    validate_max: bool | None = None

    formset_options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.relation and not self.model:
            raise ValueError(
                "Inline requires either relation or model."
            )

        if self.extra is not None and self.extra < 0:
            raise ValueError("extra cannot be negative.")

        if self.min_num is not None and self.min_num < 0:
            raise ValueError("min_num cannot be negative.")

        if self.max_num is not None and self.max_num < 0:
            raise ValueError("max_num cannot be negative.")

