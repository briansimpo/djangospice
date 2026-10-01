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

    The builder API is kept separate from the serialized HTML attribute
    state so method names such as ``get()`` and ``post()`` never collide
    with attribute storage.
    """

    # ------------------------------------------------------------------
    # Standard HTML
    # ------------------------------------------------------------------

    id: str | None = None
    css_class: str = ""
    attrs: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # HTMX Request
    # ------------------------------------------------------------------

    request_attrs: dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Swapping
    # ------------------------------------------------------------------

    target: str | None = None
    swap: str | None = None
    swap_oob: str | None = None
    select: str | None = None
    select_oob: str | None = None

    # ------------------------------------------------------------------
    # Triggers & Execution
    # ------------------------------------------------------------------

    trigger: str | None = None
    sync: str | None = None
    disable: bool | None = None
    disinherit: str | None = None

    # ------------------------------------------------------------------
    # Navigation & History
    # ------------------------------------------------------------------

    push_url: bool | str | None = None
    replace_url: bool | str | None = None
    boost: bool | None = None
    history: bool | None = None
    history_elt: bool | None = None

    # ------------------------------------------------------------------
    # Request Configuration
    # ------------------------------------------------------------------

    include: str | None = None
    params: str | None = None

    vals: dict[str, Any] | str = field(default_factory=dict)
    headers: dict[str, Any] | str = field(default_factory=dict)

    encoding: str | None = None
    ext: str | None = None

    # ------------------------------------------------------------------
    # UX & Feedback
    # ------------------------------------------------------------------

    indicator: str | None = None
    disabled_elt: str | None = None
    confirm: str | None = None
    prompt: str | None = None
    preserve: bool | None = None

    # ------------------------------------------------------------------
    # Events & WebSockets
    # ------------------------------------------------------------------

    on: dict[str, str] = field(default_factory=dict)

    ws: str | None = None
    sse: str | None = None

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------

    ATTRIBUTE_MAP: ClassVar[dict[str, str]] = {
        "target": "hx-target",
        "swap": "hx-swap",
        "swap_oob": "hx-swap-oob",
        "select": "hx-select",
        "select_oob": "hx-select-oob",

        "trigger": "hx-trigger",
        "sync": "hx-sync",
        "disable": "hx-disable",
        "disinherit": "hx-disinherit",

        "push_url": "hx-push-url",
        "replace_url": "hx-replace-url",
        "boost": "hx-boost",
        "history": "hx-history",
        "history_elt": "hx-history-elt",

        "include": "hx-include",
        "params": "hx-params",
        "encoding": "hx-encoding",
        "ext": "hx-ext",

        "indicator": "hx-indicator",
        "disabled_elt": "hx-disabled-elt",
        "confirm": "hx-confirm",
        "prompt": "hx-prompt",
        "preserve": "hx-preserve",

        "ws": "hx-ws",
        "sse": "hx-sse",
    }

    # ------------------------------------------------------------------
    # Fluent Request API
    # ------------------------------------------------------------------

    def request(self, method: HTTPMethod | str, url: str) -> Self:
        """
        Set the HTMX request method and destination URL.
        """
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

        self.request_attrs[f"hx-{method_lower}"] = url

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
    # Fluent HTMX API
    # ------------------------------------------------------------------

    def swap_to(self, strategy: str) -> Self:
        self.swap = strategy
        return self

    def target_to(self, selector: str) -> Self:
        self.target = selector
        return self

    def trigger_on(self, trigger: str) -> Self:
        self.trigger = trigger
        return self

    def include_data(self, selector: str) -> Self:
        self.include = selector
        return self

    def show_indicator(self, selector: str) -> Self:
        self.indicator = selector
        return self

    def confirm_with(self, message: str) -> Self:
        self.confirm = message
        return self

    def push(self, url: bool | str = True) -> Self:
        self.push_url = url
        return self

    # ------------------------------------------------------------------
    # Values & Headers
    # ------------------------------------------------------------------

    def with_vals(self, raw_js_str: str | None = None, **kwargs: Any) -> Self:
        """
        Add values to ``hx-vals``.

        ``raw_js_str`` can be used for native HTMX JavaScript values,
        for example::

            raw_js_str="js:{myVar: getVar()}"
        """
        if raw_js_str is not None:
            self.vals = raw_js_str
            return self

        if not isinstance(self.vals, dict):
            self.vals = {}

        self.vals.update(kwargs)

        return self

    def with_headers(self, **kwargs: Any) -> Self:
        """
        Add request headers to ``hx-headers``.
        """
        if not isinstance(self.headers, dict):
            self.headers = {}

        self.headers.update(kwargs)

        return self

    # ------------------------------------------------------------------
    # HTML Attributes
    # ------------------------------------------------------------------

    def add_class(self, *classes: str) -> Self:
        if not classes:
            return self

        current_classes = self.css_class.split()
        new_classes = [
            c
            for chunk in classes
            for c in chunk.split()
            if c
        ]

        seen: set[str] = set()

        self.css_class = " ".join(
            c
            for c in current_classes + new_classes
            if not (c in seen or seen.add(c))
        )

        return self

    def attr(self, name: str, value: Any) -> Self:
        self.attrs[name] = value
        return self

    def event(self, name: str, handler: str) -> Self:
        self.on[name] = handler
        return self

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize into the final HTML attribute dictionary.
        """
        data: dict[str, Any] = dict(self.attrs)

        if self.id:
            data["id"] = self.id

        if self.css_class:
            data["class"] = self.css_class

        # Request attributes.
        data.update(self.request_attrs)

        # Typed HTMX attributes.
        for field_name, html_name in self.ATTRIBUTE_MAP.items():
            value = getattr(self, field_name)

            if value is None:
                continue

            if isinstance(value, bool):
                data[html_name] = str(value).lower()
            else:
                data[html_name] = value

        # hx-vals
        if self.vals:
            data["hx-vals"] = (
                self.vals
                if isinstance(self.vals, str)
                else json.dumps(self.vals)
            )

        # hx-headers
        if self.headers:
            data["hx-headers"] = (
                self.headers
                if isinstance(self.headers, str)
                else json.dumps(self.headers)
            )

        # hx-on:*
        for event, handler in self.on.items():
            data[f"hx-on:{event}"] = handler

        return data


    # ------------------------------------------------------------------
    # Magic Methods
    # ------------------------------------------------------------------

    def __bool__(self) -> bool:
        return bool(
            self.id
            or self.css_class
            or self.attrs
            or self.request_attrs
            or self.vals
            or self.headers
            or self.on
            or any(
                getattr(self, field_name) is not None
                for field_name in self.ATTRIBUTE_MAP
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