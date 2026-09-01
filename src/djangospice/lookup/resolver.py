from __future__ import annotations

from django.apps import apps
from django.db import models

from .definition import LookupDefinition
from .exceptions import LookupModelNotFound


class LookupModelResolver:
    """
    Resolve Django models from app/model identifiers.
    """

    def resolve(self, app_label: str, model_name: str) -> type[models.Model]:

        model = apps.get_model(app_label, model_name)

        if model is None:
            raise LookupModelNotFound(
                f"Model '{app_label}.{model_name}' "
                "does not exist."
            )

        return model


class LookupDefinitionResolver:
    """
    Resolve the LookupDefinition for a model.

    This is the extension point for convention-over-
    configuration lookup definitions.
    """

    def resolve(
        self,
        model: type[models.Model],
    ) -> LookupDefinition:

        return LookupDefinition(
            model=model,
        )