from __future__ import annotations
from django.apps import apps
from .definition import LookupDefinition
from .registry import LookupRegistry
from .identifier import LookupIdentifier


class LookupResolver:
    """
    Resolves registered lookup definitions.
    """

    def __init__(self, registry: LookupRegistry) -> None:
        self.registry = registry

    def resolve(self, identifier: LookupIdentifier) -> LookupDefinition:
        return self.registry.get(identifier)