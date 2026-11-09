
from __future__ import annotations

from typing import Any

from django import forms
from django.db import models, transaction

from .exceptions import (
    FormAlreadySavedError,
    InvalidFormError,
)


class ModelFormProcessor:
    """
    Coordinates a parent ModelForm and its inline formsets.

    Responsibilities:
    - Construct the parent form.
    - Construct configured inline formsets.
    - Validate the complete form collection.
    - Save everything atomically.
    """

    def __init__(
        self,
        form_class: type[forms.ModelForm],
        *,
        data: Any = None,
        files: Any = None,
        instance: models.Model | None = None,
        initial: dict[str, Any] | None = None,
        prefix: str | None = None,
    ):
        if not issubclass(form_class, forms.ModelForm):
            raise TypeError(
                "form_class must inherit from ModelForm."
            )

        self.form_class = form_class
        self.data = data
        self.files = files

        self.form = form_class(
            data=data,
            files=files,
            instance=instance,
            initial=initial,
            prefix=prefix,
        )

        self.formsets = self._build_formsets()

        self._validated = False
        self._valid = False
        self._saved = False

    @property
    def instance(self) -> models.Model:
        return self.form.instance

    @property
    def is_bound(self) -> bool:
        return self.form.is_bound

    def _build_formsets(self) -> dict:
        getter = getattr(
            self.form_class,
            "get_inline_formsets",
            None,
        )

        if getter is None:
            return {}

        formset_classes = getter()
        formsets = {}

        for name, formset_class in formset_classes.items():
            # Each relationship needs a distinct prefix.
            # Include the parent prefix when one is supplied.
            prefix = (
                f"{self.form.prefix}-{name}"
                if self.form.prefix
                else name
            )

            formsets[name] = formset_class(
                data=self.data,
                files=self.files,
                instance=self.form.instance,
                prefix=prefix,
            )

        return formsets

    def is_valid(self) -> bool:
        if self._validated:
            return self._valid

        parent_valid = self.form.is_valid()

        # Evaluate every formset, even if an earlier one is invalid.
        formset_results = [
            formset.is_valid()
            for formset in self.formsets.values()
        ]

        self._valid = (
            parent_valid and all(formset_results)
        )
        self._validated = True

        return self._valid

    @property
    def errors(self) -> dict:
        return {
            "form": self.form.errors,
            "formsets": {
                name: formset.errors
                for name, formset in self.formsets.items()
            },
            "non_form_errors": {
                name: formset.non_form_errors()
                for name, formset in self.formsets.items()
                if formset.non_form_errors()
            },
        }

    def save(self) -> models.Model:
        if self._saved:
            raise FormAlreadySavedError(
                "This form processor has already saved."
            )

        if not self.is_valid():
            raise InvalidFormError(
                "Cannot save invalid forms or formsets."
            )

        with transaction.atomic():
            # Save the parent first so it has a primary key.
            instance = self.form.save(commit=False)
            instance.save()

            # Save parent many-to-many relationships.
            self.form.save_m2m()

            # Save all related objects against the saved parent.
            for formset in self.formsets.values():
                formset.instance = instance
                formset.save()

        self._saved = True
        return instance
