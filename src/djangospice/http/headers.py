from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, ClassVar, Self

from djangospice.core.serializable import Serializable

from .events import HTMXEvent
from .location import HTMXLocation


@dataclass(slots=True)
class HTMXHeaders(Serializable):
    """
    Represents HTMX response headers.

    This object is responsible for generating HTTP response headers
    understood by HTMX using a private state representation and a 
    fluent public API with short verb methods.
    """

    # ------------------------------------------------------------------
    # Private Navigation State
    # ------------------------------------------------------------------
    _redirect: str | None = None
    _location: HTMXLocation | str | None = None
    _push_url: str | bool | None = None
    _replace_url: str | bool | None = None

    # ------------------------------------------------------------------
    # Private Rendering State
    # ------------------------------------------------------------------
    _refresh: bool = False
    _retarget: str | None = None
    _reswap: str | None = None
    _focus: str | None = None

    # ------------------------------------------------------------------
    # Private Events State
    # ------------------------------------------------------------------
    _event: HTMXEvent = field(default_factory=HTMXEvent)
    _after_swap_event: HTMXEvent = field(default_factory=HTMXEvent)
    _after_settle_event: HTMXEvent = field(default_factory=HTMXEvent)

    # ------------------------------------------------------------------
    # Private Extra Headers State
    # ------------------------------------------------------------------
    _headers: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Private Mapping
    # ------------------------------------------------------------------
    _HEADER_MAP: ClassVar[dict[str, str]] = {
        "_redirect": "HX-Redirect",
        "_location": "HX-Location",
        "_push_url": "HX-Push-Url",
        "_replace_url": "HX-Replace-Url",
        "_refresh": "HX-Refresh",
        "_retarget": "HX-Retarget",
        "_reswap": "HX-Reswap",
        "_focus": "HX-Reselect",
    }

    # ------------------------------------------------------------------
    # Navigation API
    # ------------------------------------------------------------------

    @classmethod
    def get_headers(cls) -> tuple[str, ...]:
        """Return all HTMX response header names managed by this class."""
        return (
            *cls._HEADER_MAP.values(),
            "HX-Trigger",
            "HX-Trigger-After-Swap",
            "HX-Trigger-After-Settle",
        )

    def redirect(self, url: str) -> Self:
        """Redirect the client to a different URL."""
        self._redirect = url
        self._location = None
        return self

    def navigate(self, path: str, *, target: str | None = None, swap: str | None = None, select: str | None = None) -> Self:
        """Perform an HTMX client-side SPA-style navigation."""
        self._location = HTMXLocation(
            path=path,
            target=target,
            swap=swap,
            select=select,
        )
        self._redirect = None
        return self

    def push(self, url: str | bool = True) -> Self:
        """Push a new URL or enable/disable history pushing in the browser history."""
        self._push_url = url
        return self

    def replace(self, url: str | bool = True) -> Self:
        """Replace the current URL or enable/disable history replacing in the browser history."""
        self._replace_url = url
        return self

    # ------------------------------------------------------------------
    # Rendering API
    # ------------------------------------------------------------------

    def refresh(self, enabled: bool = True) -> Self:
        """Trigger a full page refresh on the client or clear it."""
        self._refresh = enabled
        return self

    def retarget(self, selector: str) -> Self:
        """Change the target element for the response swap."""
        self._retarget = selector
        return self

    def reswap(self, strategy: str) -> Self:
        """Change the swapping strategy for the response."""
        self._reswap = strategy
        return self

    def focus(self, selector: str) -> Self:
        """Focus on a specific element after the swap."""
        self._focus = selector
        return self

    # ------------------------------------------------------------------
    # Events API
    # ------------------------------------------------------------------
    
    def trigger(self, name: str, **payload: Any) -> Self:
        """Trigger an HTMX event immediately."""
        self._event.add(name, **payload)
        return self

    def swap(self, name: str, **payload: Any) -> Self:
        """Trigger an HTMX event after the swap phase."""
        self._after_swap_event.add(name, **payload)
        return self

    def settle(self, name: str, **payload: Any) -> Self:
        """Trigger an HTMX event after the settle phase."""
        self._after_settle_event.add(name, **payload)
        return self

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def set(self, name: str, value: str) -> Self:
        """Set a custom response header."""
        self._headers[name] = value
        return self

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, str]:
        headers: dict[str, str] = {}

        for field_name, header_name in self._HEADER_MAP.items():
            value = getattr(self, field_name)

            if value is None or value is False:
                continue

            if isinstance(value, bool):
                value = str(value).lower()

            headers[header_name] = str(value)

        if self._location is not None:
            if isinstance(self._location, HTMXLocation):
                headers["HX-Location"] = self._location.to_json()
            else:
                headers["HX-Location"] = self._location

        if not self._event.empty:
            headers["HX-Trigger"] = self._event.to_json()

        if not self._after_swap_event.empty:
            headers["HX-Trigger-After-Swap"] = self._after_swap_event.to_json()

        if not self._after_settle_event.empty:
            headers["HX-Trigger-After-Settle"] = self._after_settle_event.to_json()

        headers.update({
            key: str(value)
            for key, value in self._headers.items()
        })

        return headers

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def __bool__(self) -> bool:
        """Optimized truthiness validation avoiding expensive serialization chains."""
        return (
            not self._event.empty
            or not self._after_swap_event.empty
            or not self._after_settle_event.empty
            or bool(self._headers)
            or any(
                val is not None and val is not False
                for f in self._HEADER_MAP
                if (val := getattr(self, f))
            )
        )