from __future__ import annotations

from abc import ABC
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Object(ABC):
    """
    Base class for immutable value objects.
    """