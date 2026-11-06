from __future__ import annotations
from django.apps import apps
from .definition import LookupDefinition
from .registry import LookupRegistry


class LookupResolver:
    """
    Resolves registered lookup definitions.
    """

    def __init__(self, registry: LookupRegistry) -> None:
        self.registry = registry

    def resolve(self, identifier: str) -> LookupDefinition:
        return self.registry.get(identifier)