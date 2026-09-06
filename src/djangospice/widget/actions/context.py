from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from django.http import HttpRequest

from djangospice.core.payload import Payload

if TYPE_CHECKING:
    from djangospice.widgets.widget import Widget


@dataclass(slots=True)
class ActionContext:
    """
    Runtime context supplied to an Action.
    """

    widget: "Widget"

    request: HttpRequest

    object: Any | None = None

    objects: tuple[Any, ...] = ()

    data: Payload = field(default_factory=Payload)

    @property
    def user(self):
        return self.request.user

    @property
    def is_row(self) -> bool:
        return self.object is not None

    @property
    def is_bulk(self) -> bool:
        return bool(self.objects)

    @property
    def count(self) -> int:
        return len(self.objects)