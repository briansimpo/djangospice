from __future__ import annotations

from typing import Callable

from django import forms
from django.db import models
from django.core.exceptions import FieldDoesNotExist

from .fields import LookupChoiceField, LookupMultipleChoiceField
from .exceptions import InvalidLookupError
from .lookup import Lookup


def normalize_lookups(lookups=None):
    """
    Normalize Lookup declarations into a field-name mapping.
    """
    result = {}

    for lookup in lookups or ():
        if not isinstance(lookup, Lookup):
            raise InvalidLookupError(
                "lookups must contain Lookup instances."
            )

        if lookup.field_name in result:
            raise InvalidLookupError(
                f"Duplicate lookup configuration: "
                f"{lookup.field_name!r}."
            )

        result[lookup.field_name] = lookup

    return result


def validate_lookups(model, lookups):
    """
    Ensure configured lookups reference valid model fields.
    """
    for field_name, lookup in lookups.items():
        try:
            model_field = model._meta.get_field(field_name)
        except FieldDoesNotExist as exc:
            raise InvalidLookupError(
                f"{model._meta.label} has no field "
                f"named {field_name!r}."
            ) from exc

        if not isinstance(
            model_field,
            (
                models.ForeignKey,
                models.OneToOneField,
                models.ManyToManyField,
            ),
        ):
            raise InvalidLookupError(
                f"{model._meta.label}.{field_name} "
                "is not a relational model field."
            )


def create_form_field(*, model, lookups=None, auto_lookup=True, callback: Callable | None = None):
    """
    Create a callback for Django's ModelForm factory.

    Relational model fields automatically receive LookupChoiceField or
    LookupMultipleChoiceField. Explicit Lookup declarations customize
    the generated lookup field.
    """
    lookups = normalize_lookups(lookups)
    validate_lookups(model, lookups)

    def formfield_callback(db_field, **kwargs):
        formfield = (
            callback(db_field, **kwargs)
            if callback
            else db_field.formfield(**kwargs)
        )

        if formfield is None or not auto_lookup:
            return formfield

        if not isinstance(
            formfield,
            (
                forms.ModelChoiceField,
                forms.ModelMultipleChoiceField,
            ),
        ):
            return formfield

        # Respect explicitly supplied widgets and fields.
        if "widget" in kwargs:
            return formfield

        lookup = lookups.get(db_field.name)

        if lookup is None and not auto_lookup:
            return formfield

        options = dict(lookup.options) if lookup else {}

        # Preserve the generated field's queryset and Django options.
        field_class = (
            LookupMultipleChoiceField
            if isinstance(formfield, forms.ModelMultipleChoiceField)
            else LookupChoiceField
        )

        options.setdefault("queryset", formfield.queryset)

        # Preserve Django's generated field configuration.
        options.setdefault("required", formfield.required)
        options.setdefault("label", formfield.label)
        options.setdefault("help_text", formfield.help_text)
        options.setdefault("initial", formfield.initial)
        options.setdefault("validators", formfield.validators)
        options.setdefault("error_messages", formfield.error_messages)
        options.setdefault("to_field_name", formfield.to_field_name)

        return field_class(**options)

    return formfield_callback
