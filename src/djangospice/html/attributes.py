from __future__ import annotations

import json
from dataclasses import dataclass, field
from html import escape
from typing import Any, ClassVar, Literal, Self

from djangospice.core.serializable import Serializable


HTTPMethod = Literal["get", "post", "put", "patch", "delete"]


@dataclass(slots=True)
class HTMXAttributes(Serializable):
    """
    Represents HTMX attributes with a fluent builder interface.

    All attributes are private/protected and the builder API uses short,
    concise action verbs.
    """

    # ------------------------------------------------------------------
    # Standard HTML Private State
    # ------------------------------------------------------------------

    _id: str | None = None
    _css_class: str = ""
    _attrs: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # HTMX Request Private State
    # ------------------------------------------------------------------

    _request_attrs: dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Swapping Private State
    # ------------------------------------------------------------------

    _target: str | None = None
    _swap: str | None = None
    _swap_oob: str | None = None
    _select: str | None = None
    _select_oob: str | None = None

    # ------------------------------------------------------------------
    # Triggers & Execution Private State
    # ------------------------------------------------------------------

    _trigger: str | None = None
    _sync: str | None = None
    _disable: bool | None = None
    _disinherit: str | None = None

    # ------------------------------------------------------------------
    # Navigation & History Private State
    # ------------------------------------------------------------------

    _push_url: bool | str | None = None
    _replace_url: bool | str | None = None
    _boost: bool | None = None
    _history: bool | None = None
    _history_elt: bool | None = None

    # ------------------------------------------------------------------
    # Request Configuration Private State
    # ------------------------------------------------------------------

    _include: str | None = None
    _params: str | None = None

    _vals: dict[str, Any] | str = field(default_factory=dict)
    _headers: dict[str, Any] | str = field(default_factory=dict)

    _encoding: str | None = None
    _ext: str | None = None

    # ------------------------------------------------------------------
    # UX & Feedback Private State
    # ------------------------------------------------------------------

    _indicator: str | None = None
    _disabled_elt: str | None = None
    _confirm: str | None = None
    _prompt: str | None = None
    _preserve: bool | None = None

    # ------------------------------------------------------------------
    # Events & WebSockets Private State
    # ------------------------------------------------------------------

    _on: dict[str, str] = field(default_factory=dict)

    _ws: str | None = None
    _sse: str | None = None

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------

    _ATTRIBUTE_MAP: ClassVar[dict[str, str]] = {
        "_target": "hx-target",
        "_swap": "hx-swap",
        "_swap_oob": "hx-swap-oob",
        "_select": "hx-select",
        "_select_oob": "hx-select-oob",

        "_trigger": "hx-trigger",
        "_sync": "hx-sync",
        "_disable": "hx-disable",
        "_disinherit": "hx-disinherit",

        "_push_url": "hx-push-url",
        "_replace_url": "hx-replace-url",
        "_boost": "hx-boost",
        "_history": "hx-history",
        "_history_elt": "hx-history-elt",

        "_include": "hx-include",
        "_params": "hx-params",
        "_encoding": "hx-encoding",
        "_ext": "hx-ext",

        "_indicator": "hx-indicator",
        "_disabled_elt": "hx-disabled-elt",
        "_confirm": "hx-confirm",
        "_prompt": "hx-prompt",
        "_preserve": "hx-preserve",

        "_ws": "hx-ws",
        "_sse": "hx-sse",
    }

    # ------------------------------------------------------------------
    # Fluent Request API
    # ------------------------------------------------------------------

    def request(self, method: HTTPMethod | str, url: str) -> Self:
        """Set the HTMX request method and destination URL."""
        method_lower = method.lower()

        if method_lower not in {
            "get",
            "post",
            "put",
            "patch",
            "delete",
        }:
            raise ValueError(
                f"Unsupported HTMX request method: {method}"
            )

        self._request_attrs[f"hx-{method_lower}"] = url
        return self

    def get(self, url: str) -> Self:
        """Set an ``hx-get`` request."""
        return self.request("get", url)

    def post(self, url: str) -> Self:
        """Set an ``hx-post`` request."""
        return self.request("post", url)

    def put(self, url: str) -> Self:
        """Set an ``hx-put`` request."""
        return self.request("put", url)

    def patch(self, url: str) -> Self:
        """Set an ``hx-patch`` request."""
        return self.request("patch", url)

    def delete(self, url: str) -> Self:
        """Set an ``hx-delete`` request."""
        return self.request("delete", url)

    # ------------------------------------------------------------------
    # Fluent HTMX API (Short Verbs)
    # ------------------------------------------------------------------

    def swap(self, strategy: str) -> Self:
        """Set the ``hx-swap`` strategy."""
        self._swap = strategy
        return self

    def target(self, selector: str) -> Self:
        """Set the ``hx-target`` selector."""
        self._target = selector
        return self

    def trigger(self, trigger: str) -> Self:
        """Set the ``hx-trigger`` condition."""
        self._trigger = trigger
        return self

    def include(self, selector: str) -> Self:
        """Set the ``hx-include`` selector."""
        self._include = selector
        return self

    def indicator(self, selector: str) -> Self:
        """Set the ``hx-indicator`` selector."""
        self._indicator = selector
        return self

    def confirm(self, message: str) -> Self:
        """Set the ``hx-confirm`` message."""
        self._confirm = message
        return self

    def push(self, url: bool | str = True) -> Self:
        """Set the ``hx-push-url`` state."""
        self._push_url = url
        return self

    def replace(self, url: bool | str = True) -> Self:
        """Set the ``hx-replace-url`` state."""
        self._replace_url = url
        return self

    # ------------------------------------------------------------------
    # Values & Headers
    # ------------------------------------------------------------------

    def vals(self, raw_js_str: str | None = None, **kwargs: Any) -> Self:
        """Add values to ``hx-vals``."""
        if raw_js_str is not None:
            self._vals = raw_js_str
            return self

        if not isinstance(self._vals, dict):
            self._vals = {}

        self._vals.update(kwargs)
        return self

    def headers(self, **kwargs: Any) -> Self:
        """Add request headers to ``hx-headers``."""
        if not isinstance(self._headers, dict):
            self._headers = {}

        self._headers.update(kwargs)
        return self

    # ------------------------------------------------------------------
    # HTML Attributes
    # ------------------------------------------------------------------

    def add(self, *classes: str) -> Self:
        """Add CSS classes."""
        if not classes:
            return self

        current_classes = self._css_class.split()
        new_classes = [
            c
            for chunk in classes
            for c in chunk.split()
            if c
        ]

        seen: set[str] = set()

        self._css_class = " ".join(
            c
            for c in current_classes + new_classes
            if not (c in seen or seen.add(c))
        )

        return self

    def attr(self, name: str, value: Any) -> Self:
        """Set a custom HTML attribute."""
        self._attrs[name] = value
        return self

    def on(self, name: str, handler: str) -> Self:
        """Bind an event handler to ``hx-on:*``."""
        self._on[name] = handler
        return self

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize into the final HTML attribute dictionary."""
        data: dict[str, Any] = dict(self._attrs)

        if self._id:
            data["id"] = self._id

        if self._css_class:
            data["class"] = self._css_class

        # Request attributes.
        data.update(self._request_attrs)

        # Typed HTMX attributes.
        for field_name, html_name in self._ATTRIBUTE_MAP.items():
            value = getattr(self, field_name)

            if value is None:
                continue

            if isinstance(value, bool):
                data[html_name] = str(value).lower()
            else:
                data[html_name] = value

        # hx-vals
        if self._vals:
            data["hx-vals"] = (
                self._vals
                if isinstance(self._vals, str)
                else json.dumps(self._vals)
            )

        # hx-headers
        if self._headers:
            data["hx-headers"] = (
                self._headers
                if isinstance(self._headers, str)
                else json.dumps(self._headers)
            )

        # hx-on:*
        for event, handler in self._on.items():
            data[f"hx-on:{event}"] = handler

        return data

    # ------------------------------------------------------------------
    # Magic Methods
    # ------------------------------------------------------------------

    def __bool__(self) -> bool:
        return bool(
            self._id
            or self._css_class
            or self._attrs
            or self._request_attrs
            or self._vals
            or self._headers
            or self._on
            or any(
                getattr(self, field_name) is not None
                for field_name in self._ATTRIBUTE_MAP
            )
        )


class HTMLAttributeRenderer:
    """
    Render HTML attributes into an HTML-safe attribute string.

    This is the single rendering boundary for HTML attributes.
    """

    @staticmethod
    def render(
        attributes: dict[str, Any],
    ) -> str:
        parts: list[str] = []

        for name, value in attributes.items():
            if value is None:
                continue

            name = escape(
                str(name),
                quote=True,
            )

            if isinstance(value, bool):
                if value:
                    parts.append(name)
                continue

            value = escape(
                str(value),
                quote=True,
            )

            parts.append(
                f'{name}="{value}"'
            )

        return " ".join(parts)