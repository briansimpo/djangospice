from __future__ import annotations

import json
from dataclasses import dataclass, field
from html import escape
from typing import Any, ClassVar, Literal, Self

from djangospice.core.serializable import Serializable
from djangospice.core.payload import Payload

HTTPMethod = Literal["get", "post", "put", "patch", "delete"]


@dataclass(slots=True)
class HTMXAttributes(Serializable):
    """
    Represents HTMX HTML attributes.

    This class is transport-agnostic and can be used by:
    - Widgets
    - Forms
    - Components
    - Views
    - Template rendering
    """

    # ------------------------------------------------------------------
    # Standard HTML
    # ------------------------------------------------------------------
    id: str | None = None
    css_class: str = ""

    #: Additional standard HTML attributes (e.g., placeholder, name).
    attrs: Payload = field(default_factory=Payload)

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

    # Support dicts (Payload) OR raw strings for 'javascript:' evaluation
    vals: Payload | str | dict = field(default_factory=Payload)
    headers: Payload | str | dict = field(default_factory=Payload)

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
    # Events & Websockets
    # ------------------------------------------------------------------
    on: Payload = field(default_factory=Payload)
    ws: str | None = None
    sse: str | None = None

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------
    ATTRIBUTE_MAP: ClassVar[dict[str, str]] = {
        # Requests
        "get": "hx-get",
        "post": "hx-post",
        "put": "hx-put",
        "patch": "hx-patch",
        "delete": "hx-delete",
        # Swapping
        "target": "hx-target",
        "swap": "hx-swap",
        "swap_oob": "hx-swap-oob",
        "select": "hx-select",
        "select_oob": "hx-select-oob",
        # Triggers
        "trigger": "hx-trigger",
        "sync": "hx-sync",
        "disable": "hx-disable",
        "disinherit": "hx-disinherit",
        # Navigation
        "push_url": "hx-push-url",
        "replace_url": "hx-replace-url",
        "boost": "hx-boost",
        "history": "hx-history",
        "history_elt": "hx-history-elt",
        # Request configuration
        "include": "hx-include",
        "params": "hx-params",
        "encoding": "hx-encoding",
        "ext": "hx-ext",
        "ws": "hx-ws",
        "sse": "hx-sse",
        # UX
        "indicator": "hx-indicator",
        "disabled_elt": "hx-disabled-elt",
        "confirm": "hx-confirm",
        "prompt": "hx-prompt",
        "preserve": "hx-preserve",
    }

    # ------------------------------------------------------------------
    # Fluent API
    # ------------------------------------------------------------------

    def request(self, method: HTTPMethod | str, url: str) -> Self:
        """Set the HTMX request method and URL target."""
        method_lower = method.lower()
        if method_lower not in {"get", "post", "put", "patch", "delete"}:
            raise ValueError(f"Unsupported HTMX request method: {method}")
        setattr(self, method_lower, url)
        return self
    
    def get(self, url):
        return self.request("get", url)
    
    def post(self, url):
        return self.request("post", url)
    
    def put(self, url):
        return self.request("put", url)
    
    def patch(self, url):
        return self.request("path", url)
    
    def delete(self, url):
        return self.request("delete", url)

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

    def push(self, url: bool | str = True) -> Self:
        """Update the browser's history URL."""
        self.push_url = url
        return self

    def with_vals(self, raw_js_str: str | None = None, **kwargs: Any) -> Self:
        """
        Merge values into hx-vals. 
        Pass `raw_js_str="js:{myVar: getVar()}"` to evaluate native Javascript.
        """
        if raw_js_str:
            self.vals = raw_js_str
        elif isinstance(self.vals, (Payload, dict)):
            self.vals.update(kwargs)
        else:
            self.vals = Payload(kwargs)
        return self

    def add_class(self, *classes: str) -> Self:
        """Adds unique CSS classes while maintaining insertion order."""
        if not classes:
            return self

        current_classes = self.css_class.split()
        new_classes = [c for chunk in classes for c in chunk.split() if c]

        seen = set()
        unique_ordered = [
            c for c in (current_classes + new_classes)
            if not (c in seen or seen.add(c))
        ]

        self.css_class = " ".join(unique_ordered)
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
        """Serialize into HTML attributes."""
        # Load standard user-defined attrs first so they don't overwrite HTMX logic
        data: dict[str, Any] = dict(self.attrs) if self.attrs else {}

        if self.id:
            data["id"] = self.id
        if self.css_class:
            data["class"] = self.css_class

        for field_name, html_name in self.ATTRIBUTE_MAP.items():
            value = getattr(self, field_name)
            if value is None:
                continue

            # HTMX expects explicit string "true"/"false" for boolean configurations
            if isinstance(value, bool):
                data[html_name] = str(value).lower()
            else:
                data[html_name] = value

        if self.vals:
            data["hx-vals"] = self.vals if isinstance(self.vals, str) else json.dumps(self.vals)

        if self.headers:
            data["hx-headers"] = self.headers if isinstance(self.headers, str) else json.dumps(self.headers)

        for event, handler in self.on.items():
            data[f"hx-on:{event}"] = handler

        return data

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self) -> str:
        """Render fields directly to a valid HTML attribute string."""
        html_parts = []
        for key, value in self.to_dict().items():
            # Standard HTML booleans (like `disabled`, `checked` passed via `self.attrs`)
            if isinstance(value, bool):
                if value:
                    html_parts.append(key)
                continue
                
            html_parts.append(f'{key}="{escape(str(value), quote=True)}"')
            
        return " ".join(html_parts)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def __bool__(self) -> bool:
        """Optimized truthiness validation avoiding full JSON string serialization."""
        return bool(
            self.id
            or self.css_class
            or self.vals
            or self.headers
            or self.on
            or self.attrs
            or any(getattr(self, f) is not None for f in self.ATTRIBUTE_MAP)
        )

    def __html__(self) -> str:
        return self.render()

    def __str__(self) -> str:
        return self.render()