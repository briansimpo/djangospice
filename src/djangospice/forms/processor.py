
from __future__ import annotations

from typing import Any

from django import forms
from django.db import models, transaction


class ModelFormProcessor:
    """
    Coordinates a model form and its configured inline formsets.

    The parent form and all inline formsets share the same request
    data and files.
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
        self.form_class = form_class

        self.form = form_class(
            data=data,
            files=files,
            instance=instance,
            initial=initial,
            prefix=prefix,
        )

        self.formsets = self._build_formsets(
            data=data,
            files=files,
        )

    def _build_formsets(self, *, data, files) -> dict:
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
            formsets[name] = formset_class(
                data=data,
                files=files,
                instance=self.form.instance,
            )

        return formsets

    @property
    def instance(self) -> models.Model:
        return self.form.instance

    @property
    def errors(self) -> dict:
        return {
            "form": self.form.errors,
            "formsets": {
                name: formset.errors
                for name, formset in self.formsets.items()
            },
        }

    def is_valid(self) -> bool:
        parent_valid = self.form.is_valid()

        formset_results = [
            formset.is_valid()
            for formset in self.formsets.values()
        ]

        return parent_valid and all(formset_results)

    def save(self) -> models.Model:
        if not self.is_valid():
            raise ValueError(
                "Cannot save invalid form or inline formsets."
            )

        with transaction.atomic():
            # Save the parent first.
            instance = self.form.save(commit=False)
            instance.save()

            # Save parent many-to-many relationships.
            self.form.save_m2m()

            # Save related objects after the parent has a primary key.
            for formset in self.formsets.values():
                formset.instance = instance
                formset.save()

        return instance
