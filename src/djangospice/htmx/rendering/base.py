from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from django.http import HttpRequest


T = TypeVar("T")


class Renderer(ABC, Generic[T]):
    """
    Base class for internal response rendering components.
    """

    @abstractmethod
    def render(self, value: T, *, request: HttpRequest | None = None) -> str:
        raise NotImplementedError