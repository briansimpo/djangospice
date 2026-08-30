from __future__ import annotations

from django.apps import apps
from django.db.models import Field
from django.core.exceptions import FieldDoesNotExist

from .exceptions import  LookupModelNotFound, InvalidLookupField


class LookupModelResolver:

    @staticmethod
    def resolve(app_label: str, model_name: str):
        model = apps.get_model(
            app_label,
            model_name,
        )

        if model is None:
            raise LookupModelNotFound(
                f"Model '{app_label}.{model_name}' "
                "does not exist."
            )

        return model


class RelationResolver:

    @classmethod
    def resolve(cls, model, path: str) -> tuple[Field, ...]:
        """
        Resolve a Django relationship path.

        Example:

            department__faculty

        resolves:

            Program.department
                ↓
            Department.faculty
        """

        if not path:
            raise InvalidLookupField(
                "Lookup field cannot be empty."
            )

        current_model = model
        resolved: list[Field] = []

        for part in path.split("__"):

            try:
                field = current_model._meta.get_field(
                    part
                )
            except FieldDoesNotExist as exc:
                raise InvalidLookupField(
                    f"'{path}' is not a valid "
                    f"relationship on "
                    f"'{model._meta.label}'."
                ) from exc

            if not field.is_relation:
                raise InvalidLookupField(
                    f"'{path}' is not a relationship path. "
                    f"'{part}' on "
                    f"'{current_model._meta.label}' "
                    "is not relational."
                )

            resolved.append(field)
            current_model = field.related_model

        return tuple(resolved)