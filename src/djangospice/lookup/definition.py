
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, TypeAlias

from django.db import models

from djangospice.exec.identity import ClassIdentity

from .dependencies import (
    LookupDependency,
    LookupDependencyDeclaration,
    LookupDependencyResolver,
)
from .exceptions import LookupConfigurationError
from .scope import LookupScope, UserScope


LookupSearchField: TypeAlias = str


@dataclass(frozen=True, slots=True)
class LookupDefinition:
    """
    Declarative definition of a model lookup.

    A lookup can be initialized using either a model class
    or a queryset. When a queryset is supplied, its model
    is resolved automatically.
    """

    model: type[models.Model] | None = None
    queryset: models.QuerySet | None = None

    depends_on: (
        LookupDependencyDeclaration
        | Iterable[LookupDependencyDeclaration]
        | None
    ) = None

    search_fields: tuple[str, ...] = ()

    ordering: tuple[str, ...] = ()

    label_field: str | None = None

    description_field: str | None = None

    page_size: int = 20

    max_page_size: int = 100

    scope: str | None = None

    def __post_init__(self) -> None:
        model = self.model
        queryset = self.queryset

        if queryset is not None:
            if not isinstance(queryset, models.QuerySet):
                raise LookupConfigurationError(
                    "LookupDefinition.queryset must be a Django QuerySet."
                )

            queryset_model = queryset.model

            if model is not None and model is not queryset_model:
                raise LookupConfigurationError(
                    "model and queryset.model must refer to the same model."
                )

            model = queryset_model

        if model is None:
            raise LookupConfigurationError(
                "LookupDefinition requires either model or queryset."
            )

        if not isinstance(model, type) or not issubclass(
            model,
            models.Model,
        ):
            raise LookupConfigurationError(
                "LookupDefinition.model must be a Django model class."
            )

        object.__setattr__(self, "model", model)

        if self.page_size < 1:
            raise LookupConfigurationError(
                "LookupDefinition.page_size must be greater than zero."
            )

        if self.max_page_size < 1:
            raise LookupConfigurationError(
                "LookupDefinition.max_page_size must be greater than zero."
            )

        if self.page_size > self.max_page_size:
            raise LookupConfigurationError(
                "page_size cannot exceed max_page_size."
            )

        if self.scope is not None:
            if not isinstance(self.scope, str):
                raise LookupConfigurationError(
                    "LookupDefinition.scope must be a string."
                )

            if not self.scope.strip():
                raise LookupConfigurationError(
                    "LookupDefinition.scope cannot be empty."
                )

    @property
    def identity(self) -> ClassIdentity:
        return ClassIdentity.from_model(self.model)

    @property
    def app_name(self) -> str:
        return self.identity.app_name

    @property
    def model_name(self) -> str:
        return self.identity.class_name

    @property
    def identifier(self) -> str:
        return str(self.identity)

    @property
    def dependencies(self) -> tuple[LookupDependency, ...]:
        return LookupDependencyResolver.normalize(
            self.model,
            self.depends_on,
        )

    @property
    def dependency_paths(self) -> tuple[str, ...]:
        return tuple(
            dependency.path
            for dependency in self.dependencies
        )

    @property
    def lookup_scope(self) -> LookupScope | None:
        if self.scope is None:
            return None

        return UserScope(self.scope.strip())
