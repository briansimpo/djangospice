from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any
from dataclasses import dataclass
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist, AppRegistryNotReady
from django.db import models
from django.db.models import Case, IntegerField, QuerySet, When

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ModelReference:
    """
    A lightweight reference to a single Django model instance.
    """
    app_label: str
    model_name: str
    pk: Any

    @classmethod
    def from_model(cls, instance: models.Model) -> ModelReference:
        if instance.pk is None:
            raise ValueError(
                f"Cannot serialize unsaved model instance: {instance}. "
                "Ensure the model is saved to the database first."
            )

        meta = instance._meta
        return cls(
            app_label=meta.app_label,
            model_name=meta.model_name,
            pk=instance.pk,
        )

    def resolve(self) -> models.Model | None:
        """
        Resolve the reference. Returns None if the record no longer exists.
        """
        try:
            model = apps.get_model(self.app_label, self.model_name)
            return model._default_manager.get(pk=self.pk)
        except ObjectDoesNotExist:
            logger.warning(
                f"Failed to resolve {self.app_label}.{self.model_name} "
                f"with pk={self.pk}: Record does not exist."
            )
            return None
        except AppRegistryNotReady as e:
            raise RuntimeError(
                "Attempted to deserialize a Django model before the app "
                "registry was fully populated. Ensure django.setup() is called."
            ) from e


@dataclass(slots=True)
class CollectionReference:
    """
    A lazy reference to a uniform collection of Django model instances.
    """
    app_label: str
    model_name: str
    pks: tuple[Any, ...]
    ordered: bool = True

    @classmethod
    def from_queryset(cls, queryset: QuerySet) -> CollectionReference:
        model = queryset.model
        meta = model._meta
        pk_name = meta.pk.name

        # Ensure we don't accidentally evaluate a heavy QuerySet by 
        # forcing a flat values_list specifically for the PK.
        return cls(
            app_label=meta.app_label,
            model_name=meta.model_name,
            pks=tuple(queryset.values_list(pk_name, flat=True)),
            ordered=queryset.ordered,
        )

    @classmethod
    def from_models(cls, models_: Iterable[models.Model]) -> CollectionReference:
        models_list = list(models_)

        if not models_list:
            raise ValueError("Cannot serialize an empty model collection.")

        if any(obj.pk is None for obj in models_list):
            raise ValueError(
                "Cannot serialize a collection containing unsaved models."
            )

        # Assumes uniform collection
        model = models_list[0].__class__
        meta = model._meta

        return cls(
            app_label=meta.app_label,
            model_name=meta.model_name,
            pks=tuple(obj.pk for obj in models_list),
            ordered=True,
        )

    def resolve(self) -> QuerySet:
        """
        Resolve the reference into a QuerySet. 
        Note: If records were deleted, the resulting QuerySet will simply 
        be shorter than the original collection.
        """
        model = apps.get_model(self.app_label, self.model_name)
        pk_name = model._meta.pk.name

        queryset = model._default_manager.filter(**{f"{pk_name}__in": self.pks})

        if self.ordered and self.pks:
            preserved = Case(
                *[
                    When(**{pk_name: pk, "then": index})
                    for index, pk in enumerate(self.pks)
                ],
                output_field=IntegerField(),
            )
            queryset = queryset.order_by(preserved)

        return queryset
