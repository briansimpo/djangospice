from __future__ import annotations

from django import forms
from django.db import models
from django.forms import BaseInlineFormSet
from django.forms.models import inlineformset_factory, modelform_factory

from .exceptions import InvalidModelError
from .helpers import create_form_field
from .inlines import Inline
from .relations import InlineRelation, get_inline_relations



class InlineFormBuilder:

    def __init__(self, parent_model: type[models.Model], inlines: tuple | list = (), auto_discover: bool = False):
        self.parent_model = parent_model
        self.inlines = tuple(inlines)
        self.auto_discover = auto_discover

        self.relations = {
            relation.name: relation
            for relation in get_inline_relations(parent_model)
        }

    def _resolve_relation(self, inline: Inline) -> InlineRelation:
        if inline.relation:
            relation = self.relations.get(inline.relation)

            if relation is None:
                raise ValueError(
                    f"Inline relation '{inline.relation}' "
                    f"does not exist on "
                    f"{self.parent_model.__name__}."
                )

            if inline.model and relation.model is not inline.model:
                raise ValueError(
                    f"Relation '{inline.relation}' does not point "
                    f"to {inline.model.__name__}."
                )

            if inline.fk_name and relation.fk_name != inline.fk_name:
                raise ValueError(
                    f"Relation '{inline.relation}' uses "
                    f"foreign key '{relation.fk_name}', not "
                    f"'{inline.fk_name}'."
                )

            return relation

        matches = [
            relation
            for relation in self.relations.values()
            if relation.model is inline.model
        ]

        if inline.fk_name:
            matches = [
                relation
                for relation in matches
                if relation.fk_name == inline.fk_name
            ]

        if len(matches) == 1:
            return matches[0]

        if not matches:
            raise ValueError(
                f"No inline relationship from "
                f"{self.parent_model.__name__} to "
                f"{inline.model.__name__}."
            )

        raise ValueError(
            f"Multiple inline relationships from "
            f"{self.parent_model.__name__} to "
            f"{inline.model.__name__}. Specify relation or fk_name."
        )

    def _build_formset(self, relation: InlineRelation, inline: Inline) -> type[BaseInlineFormSet]:

        is_one_to_one = relation.is_one_to_one

        # Defaults depend on relationship cardinality.
        extra = inline.extra
        if extra is None:
            extra = 1 if is_one_to_one else 0

        max_num = inline.max_num
        validate_max = inline.validate_max

        if is_one_to_one:
            if max_num is not None and max_num > 1:
                raise ValueError(
                    f"One-to-one inline '{relation.name}' "
                    "cannot have max_num greater than 1."
                )

            max_num = 1
            validate_max = True

        elif validate_max is None:
            validate_max = False

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
            raise ValueError(
                "These options cannot be overridden through "
                f"formset_options: {', '.join(sorted(conflicts))}"
            )

        return inlineformset_factory(
            parent_model=self.parent_model,
            model=relation.model,
            fk_name=relation.fk_name,
            form=inline.form or forms.ModelForm,
            formset=inline.formset,
            fields=inline.fields,
            exclude=inline.exclude,
            extra=extra,
            can_delete=inline.can_delete,
            can_delete_extra=inline.can_delete_extra,
            min_num=inline.min_num,
            max_num=max_num,
            validate_min=inline.validate_min,
            validate_max=validate_max,
            **options,
        )

    def build(self) -> dict[str, type[BaseInlineFormSet]]:
        configurations: dict[str, Inline] = {}

        # Automatically configure all discovered relationships.
        if self.auto_discover:
            for name in self.relations:
                configurations[name] = Inline(relation=name)

        # Explicit configurations override automatically discovered ones.
        for inline in self.inlines:
            if not isinstance(inline, Inline):
                raise TypeError(
                    "Inline configurations must be Inline instances."
                )

            relation = self._resolve_relation(inline)
            configurations[relation.name] = inline

        return {
            name: self._build_formset(
                self.relations[name],
                inline,
            )
            for name, inline in configurations.items()
        }


class ModelFormBuilder:

    def __init__(
        self,
        model,
        *,
        fields="__all__",
        exclude=None,
        form=None,
        lookups=None,
        auto_lookup=True,
        formfield_callback=None,
        widgets=None,
        labels=None,
        help_texts=None,
        error_messages=None,
        field_classes=None,
        inlines=None,
        auto_inlines=False,
    ):
        if not hasattr(model, "_meta"):
            raise InvalidModelError(
                f"{model!r} is not a Django model."
            )

        self.model = model
        self.fields = fields
        self.exclude = exclude
        self.form = form or forms.ModelForm

        self.lookups = lookups or []
        self.auto_lookup = auto_lookup

        self.formfield_callback = create_form_field(
            model=model,
            lookups=self.lookups,
            auto_lookup=auto_lookup,
            callback=formfield_callback,
        )

        self.widgets = widgets
        self.labels = labels
        self.help_texts = help_texts
        self.error_messages = error_messages
        self.field_classes = field_classes
        self.inlines = list(inlines or ())
        self.auto_inlines = auto_inlines

    def build(self, name="DynamicModelForm"):
        return modelform_factory(
            model=self.model,
            form=self.form,
            fields=self.fields,
            exclude=self.exclude,
            formfield_callback=self.formfield_callback,
            widgets=self.widgets,
            labels=self.labels,
            help_texts=self.help_texts,
            error_messages=self.error_messages,
            field_classes=self.field_classes,
        )

    def build_inlines(self):
        from .inlines import InlineFormBuilder

        return InlineFormBuilder(
            parent_model=self.model,
            inlines=self.inlines,
            auto_discover=self.auto_inlines,
        ).build()

    @classmethod
    def create(cls, model, **kwargs):
        return cls(model, **kwargs).build()