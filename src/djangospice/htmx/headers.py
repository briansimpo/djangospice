from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, ClassVar, Self

from djangospice.core.serializable import Serializable

from .events import Event
from .location import HTMXLocation


@dataclass(slots=True)
class HTMXHeaders(Serializable):
    """
    Represents HTMX response headers.

    This object is responsible for generating HTTP response headers
    understood by HTMX.

    Example
    -------
    >>> headers = Headers()
    >>> headers.redirect_to("/dashboard/")
    >>> headers.on("saved", id=1)
    >>> headers.apply(response)
    """

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    redirect: str | None = None
    location: HTMXLocation | str | None = None
    push_url: str | bool | None = None
    replace_url: str | bool | None = None

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    refresh: bool = False
    retarget: str | None = None
    reswap: str | None = None
    focus: str | None = None

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    event: Event = field(default_factory=Event)
    after_swap_event: Event = field(default_factory=Event)
    after_settle_event: Event = field(default_factory=Event)

    # ------------------------------------------------------------------
    # Extra Headers
    # ------------------------------------------------------------------
    headers: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------
    HEADER_MAP: ClassVar[dict[str, str]] = {
        "redirect": "HX-Redirect",
        "location": "HX-Location",
        "push_url": "HX-Push-Url",
        "replace_url": "HX-Replace-Url",
        "refresh": "HX-Refresh",
        "retarget": "HX-Retarget",
        "reswap": "HX-Reswap",
        "focus": "HX-Reselect",
    }

    # ------------------------------------------------------------------
    # Navigation API
    # ------------------------------------------------------------------

    def redirect_to(self, url: str) -> Self:
        self.redirect = url
        self.location = None
        return self

    def navigate(
        self,
        path: str,
        *,
        target: str | None = None,
        swap: str | None = None,
        select: str | None = None,
    ) -> Self:
        self.location = HTMXLocation(
            path=path,
            target=target,
            swap=swap,
            select=select,
        )
        self.redirect = None
        return self

    def push(self, url: str | bool = True) -> Self:
        self.push_url = url
        return self

    def replace(self, url: str | bool = True) -> Self:
        self.replace_url = url
        return self

    # ------------------------------------------------------------------
    # Rendering API
    # ------------------------------------------------------------------

    def refresh_page(self) -> Self:
        self.refresh = True
        return self

    def retarget_to(self, selector: str) -> Self:
        self.retarget = selector
        return self

    def reswap_to(self, strategy: str) -> Self:
        self.reswap = strategy
        return self

    def focus_on(self, selector: str) -> Self:
        self.focus = selector
        return self

    # ------------------------------------------------------------------
    # Events API
    # ------------------------------------------------------------------
    
    def trigger(self, name: str, /, **payload: Any) -> Self:
        self.event.add(name, **payload)
        return self

    def after_swap(self, name: str, /, **payload: Any) -> Self:
        self.after_swap_event.add(name, **payload)
        return self

    def after_settle(self, name: str, /, **payload: Any) -> Self:
        self.after_settle_event.add(name, **payload)
        return self


    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def header(self, name: str, value: str) -> Self:
        """Add a custom response header."""
        self.headers[name] = value
        return self

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, str]:
        """
        Serialize into HTTP headers.
        """
        headers: dict[str, str] = {}

        for field_name, header_name in self.HEADER_MAP.items():
            value = getattr(self, field_name)

            if value is None or value is False:
                continue

            if value is True:
                value = "true"
            elif hasattr(value, "to_json"):
                value = value.to_json()
            elif isinstance(value, Serializable) and hasattr(value, "to_dict"):
                value = json.dumps(value.to_dict())

            headers[header_name] = str(value)

        if not self.event.empty:
            headers["HX-Trigger"] = self.event.to_json()

        if not self.after_swap_event.empty:
            headers["HX-Trigger-After-Swap"] = self.after_swap_event.to_json()

        if not self.after_settle_event.empty:
            headers["HX-Trigger-After-Settle"] = self.after_settle_event.to_json()

        if self.headers:
            headers.update(self.headers)

        return headers

    def apply(self, response: Any) -> Any:
        """
        Apply the HTMX headers to a Django HttpResponse.
        """
        response.headers.update(self.to_dict())
        return response

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def __bool__(self) -> bool:
        """Optimized truthiness validation avoiding expensive serialization chains."""
        return (
            not self.event.empty
            or not self.after_swap_event.empty
            or not self.after_settle_event.empty
            or bool(self.headers)
            or any(
                val is not None and val is not False
                for f in self.HEADER_MAP
                if (val := getattr(self, f))
            )
        )