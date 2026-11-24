from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .nodes import ElementNode


class AttributeDirective(ABC):
    """
    Base contract for generic HTML attribute directives.

    Implementations receive an element, the attribute value,
    and an optional context object.
    """

    name: str

    @abstractmethod
    def compile(
        self,
        node: ElementNode,
        value: str | None,
        context: Any,
    ) -> None:
        ...