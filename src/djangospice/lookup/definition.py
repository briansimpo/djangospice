from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, TypeAlias

from django.db import models

from .dependencies import (
    LookupDependency,
    LookupDependencyDeclaration,
    LookupDependencyResolver,
)
from .exceptions import LookupConfigurationError


LookupSearchField: TypeAlias = str


@dataclass(frozen=True, slots=True)
class LookupDefinition:
    """
    Declarative definition of a model lookup.

    This is the reusable configuration consumed by:

        - LookupEngine
        - LookupWidget
        - Django Forms adapters
        - django-filter adapters
        - HTTP lookup endpoints
    """

    model: type[models.Model]

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

    def __post_init__(self):
        if not isinstance(
            self.model,
            type,
        ) or not issubclass(
            self.model,
            models.Model,
        ):
            raise LookupConfigurationError(
                "LookupDefinition.model must be a Django "
                "model class."
            )

        if self.page_size < 1:
            raise LookupConfigurationError(
                "LookupDefinition.page_size must be "
                "greater than zero."
            )

        if self.max_page_size < 1:
            raise LookupConfigurationError(
                "LookupDefinition.max_page_size must be "
                "greater than zero."
            )

        if self.page_size > self.max_page_size:
            raise LookupConfigurationError(
                "page_size cannot exceed max_page_size."
            )

    @property
    def dependencies(self) -> tuple[LookupDependency, ...]:
        """
        Lazily normalize depends_on.

        This is intentionally a property rather than a field,
        keeping the public API declarative.
        """

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