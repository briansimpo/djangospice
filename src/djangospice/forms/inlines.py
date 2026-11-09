
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django import forms
from django.db import models
from django.forms import BaseInlineFormSet, inlineformset_factory

from .exceptions import InvalidInlineError
from .relations import InlineRelation, get_inline_relations


@dataclass
class Inline:
    """
    Declare a related model inline.

    Examples:

        Inline("employees", extra=1)

        Inline(
            model=Employee,
            fk_name="department",
            fields=["name", "email"],
        )
    """

    relation: str | None = None
    model: type[models.Model] | None = None
    fk_name: str | None = None

    form: type[forms.ModelForm] | None = None
    formset: type[BaseInlineFormSet] = BaseInlineFormSet

    fields: Any = "__all__"
    exclude: Any = None

    extra: int = 0
    can_delete: bool = True
    can_delete_extra: bool = True

    min_num: int | None = None
    max_num: int | None = None
    validate_min: bool = False
    validate_max: bool = False

    formset_options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.relation and self.model is None:
            raise ValueError(
                "Inline requires a relation name or model."
            )

        if self.extra < 0:
            raise ValueError("Inline extra cannot be negative.")

        if self.min_num is not None and self.min_num < 0:
            raise ValueError("min_num cannot be negative.")

        if self.max_num is not None and self.max_num < 0:
            raise ValueError("max_num cannot be negative.")


class InlineFormBuilder:
    """
    Build Django inline formset classes for a parent model.
    """

    def __init__(self, parent_model: type[models.Model], *, inlines=None, auto_discover: bool = False):
        self.parent_model = parent_model
        self.inline_definitions = list(inlines or ())
        self.auto_discover = auto_discover

        self.relations = get_inline_relations(parent_model)

    def discover(self) -> list[InlineRelation]:
        return list(self.relations)

    def _resolve(self, declaration: Inline | str | type[models.Model]) -> tuple[Inline, InlineRelation]:

        if isinstance(declaration, str):
            declaration = Inline(relation=declaration)

        elif (
            isinstance(declaration, type)
            and issubclass(declaration, models.Model)
        ):
            declaration = Inline(model=declaration)

        if not isinstance(declaration, Inline):
            raise InvalidInlineError(
                "Inline declarations must be Inline instances, "
                "relationship names, or model classes."
            )

        matches = list(self.relations)

        if declaration.relation:
            matches = [
                item for item in matches
                if item.name == declaration.relation
            ]

        if declaration.model is not None:
            matches = [
                item for item in matches
                if item.model is declaration.model
            ]

        if declaration.fk_name:
            matches = [
                item for item in matches
                if item.fk_name == declaration.fk_name
            ]

        if not matches:
            raise InvalidInlineError(
                f"Cannot resolve inline {declaration!r} "
                f"for {self.parent_model._meta.label}."
            )

        if len(matches) > 1:
            raise InvalidInlineError(
                "Multiple relationships match this inline. "
                "Specify relation or fk_name to disambiguate."
            )

        return declaration, matches[0]

    def _get_definitions(self):
        definitions = {}

        if self.auto_discover:
            for relation in self.relations:
                definitions[relation.name] = (
                    Inline(relation=relation.name),
                    relation,
                )

        explicit_names = set()

        for declaration in self.inline_definitions:
            inline, relation = self._resolve(declaration)

            if relation.name in explicit_names:
                raise InvalidInlineError(
                    f"Duplicate inline declaration: {relation.name!r}."
                )

            explicit_names.add(relation.name)

            # Explicit declarations customize auto-discovered inlines.
            definitions[relation.name] = (inline, relation)

        return definitions

    def build(self):
        """Return formset classes keyed by relationship name."""

        formsets = {}

        for name, (inline, relation) in self._get_definitions().items():
            options = dict(inline.formset_options)

            reserved = {
                "parent_model",
                "model",
                "fk_name",
                "form",
                "formset",
                "fields",
                "exclude",
                "extra",
                "can_delete",
                "can_delete_extra",
                "min_num",
                "max_num",
                "validate_min",
                "validate_max",
            }

            conflicts = reserved.intersection(options)

            if conflicts:
                raise InvalidInlineError(
                    "These options must be configured directly on Inline: "
                    + ", ".join(sorted(conflicts))
                )

            formset_class = inlineformset_factory(
                parent_model=self.parent_model,
                model=relation.model,
                fk_name=relation.fk_name,
                form=inline.form or forms.ModelForm,
                formset=inline.formset,
                fields=inline.fields,
                exclude=inline.exclude,
                extra=inline.extra,
                can_delete=inline.can_delete,
                can_delete_extra=inline.can_delete_extra,
                min_num=inline.min_num,
                max_num=inline.max_num,
                validate_min=inline.validate_min,
                validate_max=inline.validate_max,
                **options,
            )

            formsets[name] = formset_class

        return formsets
