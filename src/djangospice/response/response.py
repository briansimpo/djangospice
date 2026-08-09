from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self

from djangospice.core.serializable import Serializable
from djangospice.core.payload import Payload
from djangospice.html.fragments import HTMLFragment, HTMLFragments
from .document import Document
from .headers import HTMXHeaders


@dataclass(slots=True, kw_only=True)
class Response(Serializable):
    """
    Transport-independent UI response descriptor.

    This class does not replace Django's `HttpResponse`. Instead, it describes
    what should be rendered, allowing an upstream renderer to convert this state
    into the appropriate transport format (HTML, HTMX, JSON, etc.).
    """

    # ------------------------------------------------------------------
    # Document Metadata
    # ------------------------------------------------------------------

    #: Document/page HTML title.
    title: str | None = None

    #: Document description meta tag.
    description: str | None = None

    #: Path to the primary rendering template.
    template: str | None = None

    #: Associated HTTP status code.
    status: int = 200

    # ------------------------------------------------------------------
    # Rendering Contexts
    # ------------------------------------------------------------------

    #: Template context data / JSON response payload.
    payload: Payload = field(default_factory=Payload)

    #: HTMX response header directives.
    htmx: HTMXHeaders = field(default_factory=HTMXHeaders)

    #: Out-of-band (OOB) template fragments.
    fragments: HTMLFragments = field(default_factory=HTMLFragments)
    
    document: Document = field(default_factory=Document)

    # ------------------------------------------------------------------
    # Payload Management API
    # ------------------------------------------------------------------

    def update(self, **payload: Any) -> Self:
        """
        Update multiple values in the response payload context.
        """
        self.payload.update(payload)
        return self

    def set(self, key: str, value: Any) -> Self:
        """
        Set or overwrite a single key-value pair in the response payload.
        """
        self.payload[key] = value
        return self

    # ------------------------------------------------------------------
    # Fragments Management API
    # ------------------------------------------------------------------

    def add_fragment(self, fragment: HTMLFragment) -> Self:
        """
        Append a single Out-of-Band fragment to the response.
        """
        self.fragments.add(fragment)
        return self

    def extend_fragments(self, *fragments: HTMLFragment) -> Self:
        """
        Append multiple Out-of-Band fragments to the response.
        """
        self.fragments.extend(*fragments)
        return self

    def clear_fragments(self) -> Self:
        """
        Evict all Out-of-Band fragments currently registered.
        """
        self.fragments.clear()
        return self

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def make(cls, template: str, **payload: Any) -> Self:
        """
        Factory method to instantiate a standard template-driven UI response.
        """
        return cls(
            template=template,
            payload=Payload(payload),
        )

    @classmethod
    def empty(cls, *, status: int = 200) -> Self:
        """
        Factory method to instantiate a blank/empty response context.
        """
        return cls(status=status)

    # ------------------------------------------------------------------
    # Convenience Protocols & Helpers
    # ------------------------------------------------------------------

    @property
    def has_template(self) -> bool:
        """Returns True if a primary rendering template is set."""
        return bool(self.template)

    @property
    def has_fragments(self) -> bool:
        """Returns True if there are any Out-of-Band fragments registered."""
        return bool(self.fragments)

    @property
    def is_htmx(self) -> bool:
        """
        Returns True if this response triggers HTMX client-side actions.
        """
        return bool(self.htmx)

    @property
    def is_empty(self) -> bool:
        """
        Returns True if the response contains no templates, payloads,
        out-of-band fragments, or active HTMX response headers.
        """
        return (
            not self.template
            and not self.payload
            and not self.fragments
            and not self.htmx
        )

    def __bool__(self) -> bool:
        """Enables native pythonic lifecycle checks (e.g., `if response:`)."""
        return not self.is_empty