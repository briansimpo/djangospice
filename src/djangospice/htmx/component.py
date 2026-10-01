from __future__ import annotations

import hashlib

from dataclasses import dataclass, field
from typing import Any, ClassVar
from urllib.parse import urlencode
from html import escape

from django.db.models import Model
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.safestring import SafeString, mark_safe

from djangospice.core.serializable import Serializable

from .attributes import HTMLAttributeRenderer, HTMXAttributes


@dataclass
class HTMLComponent(Serializable):
    """
    Base class for server-rendered HTML components.

    A component can render in one of two ways:

    1. Template-based rendering::

        class UserCard(HTMLComponent):
            template_name = "components/user_card.html"

            def get_context(self):
                context = super().get_context()
                context["user"] = self.user
                return context

    2. Direct-content rendering::

        class Divider(HTMLComponent):

            def get_content(self):
                return "<hr>"

    ``template_name`` is therefore optional. A component only needs to
    provide either a template or direct content.
    """

    # ------------------------------------------------------------------
    # Presentation Configuration
    # ------------------------------------------------------------------

    template_name: ClassVar[str | None] = None

    context: dict[str, Any] = field(default_factory=dict)

    # Standard HTML attributes.
    attrs: dict[str, Any] = field(default_factory=dict)

    # HTMX attributes.
    htmx: HTMXAttributes = field(
        default_factory=HTMXAttributes
    )

    css_class: str = ""

    # Runtime/state parameters used for deterministic identity.
    kwargs: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Hashing & Identification
    # ------------------------------------------------------------------

    def _serialize_for_hash(self, value: Any) -> str:
        """
        Safely serialize a value for deterministic state hashing.
        """
        if isinstance(value, Model):
            return f"{value.__class__.__name__}:{value.pk}"

        if isinstance(
            value,
            (int, float, str, bool, type(None)),
        ):
            return str(value)

        if isinstance(value, (list, tuple)):
            return (
                "["
                + ",".join(
                    self._serialize_for_hash(item)
                    for item in value
                )
                + "]"
            )

        return value.__class__.__name__

    def _generate_state_hash(
        self,
        exclude_keys: set[str] | None = None,
    ) -> str:
        """
        Generate a deterministic hash from component state.
        """
        exclude = exclude_keys or {"id"}

        state_pairs = sorted(
            (
                key,
                self._serialize_for_hash(value),
            )
            for key, value in self.kwargs.items()
            if key not in exclude
        )

        state = urlencode(state_pairs)

        if not state:
            return ""

        return hashlib.sha1(
            state.encode()
        ).hexdigest()[:8]

    @property
    def id(self) -> str:
        """
        Return a deterministic HTML ID based on component state.

        An explicit ``id`` passed through ``kwargs`` always takes
        precedence.
        """
        explicit_id = self.kwargs.get("id")

        if explicit_id:
            return str(explicit_id)

        name = getattr(
            self,
            "name",
            self.__class__.__name__.lower(),
        )

        safe_name = str(name).replace("_", "-")
        digest = self._generate_state_hash()

        return (
            f"{safe_name}-{digest}"
            if digest
            else safe_name
        )

    # ------------------------------------------------------------------
    # HTML Attributes
    # ------------------------------------------------------------------

    @property
    def html_attributes(self) -> dict[str, Any]:
        """
        Return the complete attribute mapping for the component.

        This method composes standard HTML attributes, subclass-provided
        attributes, and HTMX attributes. It does not render HTML.
        """
        attributes = dict(self.attrs)

        attributes.update(
            self.get_extra_attributes()
        )

        if self.id:
            attributes["id"] = self.id

        if self.css_class:
            attributes["class"] = self.css_class

        attributes.update(
            self.htmx.to_dict()
        )

        return attributes

    @property
    def rendered_attributes(self) -> SafeString:
        """
        Return the component's attributes rendered as safe HTML.
        """
        return mark_safe(
            HTMLAttributeRenderer.render(
                self.html_attributes
            )
        )
 
    def get_extra_attributes(self) -> dict[str, Any]:
        """
        Hook for subclasses to provide additional HTML attributes.
        """
        return {}

    # ------------------------------------------------------------------
    # Template & Context
    # ------------------------------------------------------------------

    def get_template(self) -> str | None:
        """
        Return the component template.

        ``None`` means the component is intended to render direct
        content instead of a template.
        """
        return self.template_name

    def get_context(self) -> dict[str, Any]:
        """
        Build the base template context.

        ``attrs`` contains the rendered HTML attribute string rather
        than the raw attribute dictionary.
        """
        context = dict(self.context)

        context["html_attrs"] = self.rendered_attributes

        context.update(self.kwargs)

        return context

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    def get_content(self) -> str | SafeString | None:
        """
        Return direct HTML content.

        Return ``None`` to use template-based rendering.

        Direct content should be HTML suitable for insertion into the
        rendered page.
        """
        return None

    # ------------------------------------------------------------------
    # Assets
    # ------------------------------------------------------------------

    def get_assets(self) -> dict[str, list[str]]:
        """
        Return assets required by the component.

        Example::

            return {
                "js": ["js/chart.js"],
                "css": ["css/chart.css"],
            }
        """
        return {
            "js": [],
            "css": [],
        }

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_template(
        self,
        template: str,
        context: dict[str, Any],
        *,
        request: HttpRequest | None = None,
    ) -> SafeString:
        """
        Render a template using the component context.
        """
        return mark_safe(
            render_to_string(
                template_name=template,
                context=context,
                request=request,
            )
        )

    def render_content(
        self,
        content: str | SafeString,
    ) -> SafeString:
        """
        Render direct component content.
        """
        if isinstance(content, SafeString):
            return content

        return mark_safe(content)

    def render(
        self,
        request: HttpRequest | None = None,
    ) -> SafeString:
        """
        Render the component.

        Rendering follows this order:

        1. Direct content from ``get_content()``.
        2. Template from ``get_template()`` with ``get_context()``.
        3. Raise an error if neither is available.
        """
        content = self.get_content()

        if content is not None:
            return self.render_content(content)

        template = self.get_template()

        if template:
            return self.render_template(
                template,
                self.get_context(),
                request=request,
            )

        raise ValueError(
            f"{self.__class__.__name__} must define either "
            "'template_name' or override 'get_content()'."
        )

    # ------------------------------------------------------------------
    # HTML Protocol
    # ------------------------------------------------------------------

    def __html__(self) -> SafeString:
        return self.render()

    def __str__(self) -> str:
        return str(self.render())