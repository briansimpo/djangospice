import hashlib
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model

from djangospice.core.serializable import Serializable
from djangospice.core.payload import Payload

from .attributes import HTMXAttributes


@dataclass
class HTMLComponent(Serializable):
    """
    Shared UI logic for deterministic ID generation, safe state hashing, 
    and unified rendering pipelines.
    """
    
    template_name: str | None = None
    context: Payload = field(default_factory=Payload)
    attrs: Payload = field(default_factory=Payload)
    htmx: HTMXAttributes = field(default_factory=HTMXAttributes)
    css_class: str = ""
    
    # State tracking moved to base for universal ID/Cache generation
    kwargs: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Hashing & Identification
    # ------------------------------------------------------------------

    def _serialize_for_hash(self, value: Any) -> str:
        """Safely stringifies values to guarantee deterministic hashes."""
        if isinstance(value, Model):
            return f"{value.__class__.__name__}:{value.pk}"
        if isinstance(value, (int, float, str, bool, type(None))):
            return str(value)
        if isinstance(value, (list, tuple)):
            return f"[{','.join(self._serialize_for_hash(i) for i in value)}]"
        return value.__class__.__name__

    def _generate_state_hash(self, exclude_keys: set[str] | None = None) -> str:
        """DRY helper for hashing component state."""
        exclude = exclude_keys or {"id"}
        state_pairs = sorted(
            (k, self._serialize_for_hash(v))
            for k, v in self.kwargs.items()
            if k not in exclude
        )
        state = urlencode(state_pairs)
        return hashlib.sha1(state.encode()).hexdigest()[:8] if state else ""

    @property
    def id(self) -> str:
        """Generates a deterministic, static ID based on the component's state."""
        if explicit_id := self.kwargs.get("id"):
            return str(explicit_id)

        name = getattr(self, "name", self.__class__.__name__.lower())
        safe_name = name.replace("_", "-")
        digest = self._generate_state_hash()
        
        return f"{safe_name}-{digest}" if digest else safe_name

    # ------------------------------------------------------------------
    # HTML & Rendering Pipeline
    # ------------------------------------------------------------------

    @property
    def html_attributes(self) -> dict[str, Any]:
        """Combined HTML + HTMX attributes."""
        combined = dict(self.attrs)
        
        if self.id:
            combined["id"] = self.id
        if self.css_class:
            combined["class"] = self.css_class
            
        # Merge HTMX dict safely
        combined.update(self.htmx.to_dict())
        return combined

    def get_template(self) -> str:
        if not self.template_name:
            raise ImproperlyConfigured(f"{self.__class__.__name__} must define a template.")
        return self.template_name

    def get_context(self) -> dict[str, Any]:
        """Build the base template context."""
        ctx = Payload(self.context)
        ctx["attrs"] = self.html_attributes
        ctx.update(self.kwargs)
        return ctx
    
    def get_assets(self) -> dict[str, list[str]]:
        """
        Override this to return required assets.
        Example: return {"js": ["js/chart.js"], "css": ["css/chart.css"]}
        """
        return {"js": [], "css": []}
    
    def get_content(self) -> dict[str, Any] | str | None:
        """
        Optional hook to provide dynamic content.
        - Returns a dict: Merged into standard context.
        - Returns a str: Rendered as direct HTML.
        - Returns None: Default behavior (uses standard template + context).
        """
        return None

    def render(self, request: HttpRequest | None = None) -> str:
        """Universal render method for all UI components."""
        return render_to_string(
            self.get_template(),
            self.get_context(),
            request=request,
        )

    def __html__(self):
        return mark_safe(self.render())

    def __str__(self):
        return self.render()