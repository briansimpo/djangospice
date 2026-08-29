from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(eq=False, slots=True, kw_only=True)
class Entity(ABC):
    """
    Base class for domain entities.

    Entities are identified by their id rather than by all
    of their attributes.
    """

    id: UUID = field(default_factory=uuid4)
    name: str | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented

        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return self.name or str(self.id)

