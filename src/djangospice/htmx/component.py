
from __future__ import annotations

from typing import Any, ClassVar, Iterable

from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.html import conditional_escape
from django.utils.safestring import SafeString, mark_safe

from .attributes import HTMLAttributeRenderer, HTMXAttributes


class Component:
    """
    Base class for composable UI components.

    Provides component lifecycle, composition, attributes,
    request propagation, context and rendering.
    """

    template_name: ClassVar[str | None] = None

    def __init__(
        self,
        *children: Any,
        request: HttpRequest | None = None,
        parent: Component | None = None,
        slots: dict[str, list[Component]] | None = None,
        context: dict[str, Any] | None = None,
        attributes: dict[str, Any] | None = None,
        htmx: HTMXAttributes | None = None,
        css_class: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__()

        self.request = request
        self.parent = None

        self.context = context or {}
        self.attributes = attributes or {}
        self.htmx = htmx or HTMXAttributes()
        self.css_class = css_class
        self.kwargs = kwargs

        self.children = []
        self.slots = {}

        self.add_children(*children)

        for name, components in (slots or {}).items():
            self.set_slot(name, *components)

        if isinstance(parent, Component):
            parent.add_child(self)

    # --------------------------------------------------------
    # Lifecycle
    # --------------------------------------------------------

    def initialize(self) -> None:
        """Initialize the component."""

    def configure(self) -> None:
        """Configure component attributes and interactions."""

    # --------------------------------------------------------
    # Attributes
    # --------------------------------------------------------

    def get_extra_attributes(self) -> dict[str, Any]:
        return {}

    def get_html_attributes(self) -> dict[str, Any]:
        attributes = {
            **self.attributes,
            **self.get_extra_attributes(),
        }

        if self.id:
            attributes["id"] = self.id

        if self.css_class:
            attributes["class"] = self.css_class

        attributes.update(self.htmx.to_dict())

        return attributes

    @property
    def id(self) -> str:
        explicit_id = self.kwargs.get("id")

        if explicit_id:
            return explicit_id

        name = self.attributes.get("name") or type(self).__name__.lower()
        return str(name).replace("_", "-")

    @property
    def attr(self) -> SafeString:
        return mark_safe(
            HTMLAttributeRenderer.render(self.get_html_attributes())
        )

    # --------------------------------------------------------
    # Composition
    # --------------------------------------------------------

    def add_child(self, child: Any) -> Any:
        self._attach(child)
        self.children.append(child)
        return child

    def add_children(self, *children: Any) -> tuple[Any, ...]:
        for child in children:
            self.add_child(child)

        return children

    def remove_child(self, child: Any) -> None:
        if child not in self.children:
            return

        self.children.remove(child)

        if isinstance(child, Component) and child.parent is self:
            child.parent = None

    def clear_children(self) -> None:
        for child in self.children:
            if isinstance(child, Component) and child.parent is self:
                child.parent = None

        self.children.clear()

    def get_children(self) -> tuple[Any, ...]:
        return tuple(self.children)

    # --------------------------------------------------------
    # Slots
    # --------------------------------------------------------

    def set_slot(self, name: str, *children: Any) -> None:
        self.clear_slot(name)

        for child in children:
            self.add_to_slot(name, child)

    def add_to_slot(self, name: str, child: Any) -> Any:
        self._attach(child)
        self.slots.setdefault(name, []).append(child)
        return child

    def add_to_slots(self, **slots: Any) -> None:
        for name, value in slots.items():
            if isinstance(value, (list, tuple)):
                self.set_slot(name, *value)
            else:
                self.set_slot(name, value)

    def get_slot(self, name: str) -> tuple[Any, ...]:
        return tuple(self.slots.get(name, ()))

    def has_slot(self, name: str) -> bool:
        return bool(self.slots.get(name))

    def remove_from_slot(self, name: str, child: Any) -> None:
        children = self.slots.get(name)

        if not children or child not in children:
            return

        children.remove(child)

        if isinstance(child, Component) and child.parent is self:
            child.parent = None

        if not children:
            self.slots.pop(name, None)

    def clear_slot(self, name: str) -> None:
        for child in self.slots.get(name, ()):
            if isinstance(child, Component) and child.parent is self:
                child.parent = None

        self.slots.pop(name, None)

    def clear_slots(self) -> None:
        for name in tuple(self.slots):
            self.clear_slot(name)

    # --------------------------------------------------------
    # Parent and request
    # --------------------------------------------------------

    def _attach(self, child: Any) -> None:
        if not isinstance(child, Component):
            return

        if child is self:
            raise ValueError("A component cannot contain itself.")

        parent = self

        while parent is not None:
            if parent is child:
                raise ValueError("Circular component hierarchy detected.")

            parent = parent.parent

        if child.parent is not None:
            child.parent._detach(child)

        child.parent = self

        if child.request is None:
            child.set_request(self.request)

    def _detach(self, child: Component) -> None:
        if child in self.children:
            self.children.remove(child)

        for name, children in tuple(self.slots.items()):
            if child in children:
                children.remove(child)

            if not children:
                self.slots.pop(name, None)

        if child.parent is self:
            child.parent = None

    def set_request(self, request: HttpRequest | None) -> None:
        self.request = request

        for child in self._iter_components():
            if child.request is None:
                child.set_request(request)

    def _iter_components(self):
        for child in self.children:
            if isinstance(child, Component):
                yield child

        for children in self.slots.values():
            for child in children:
                if isinstance(child, Component):
                    yield child

    # --------------------------------------------------------
    # Content and context
    # --------------------------------------------------------

    def get_content(self) -> Any:
        return None

    def get_template(self) -> str | None:
        return self.template_name

    def get_context(self) -> dict[str, Any]:
        return {
            **self.context,
            **self.kwargs,
            "component": self,
            "request": self.request,
            "children": self.get_children(),
            "slots": self.slots,
        }

    # --------------------------------------------------------
    # Rendering
    # --------------------------------------------------------

    def render_child(
        self,
        child: Any,
        request: HttpRequest | None = None,
    ) -> SafeString:
        if child is None:
            return mark_safe("")

        if isinstance(child, Component):
            return child.render(request=request)

        if isinstance(child, (list, tuple)):
            return self.render_children(child, request=request)

        return conditional_escape(child)

    def render_children(
        self,
        children: Iterable[Any] | None = None,
        request: HttpRequest | None = None,
    ) -> SafeString:
        children = self.get_children() if children is None else children

        return mark_safe(
            "".join(
                str(self.render_child(child, request))
                for child in children
            )
        )

    def render_slot(
        self,
        name: str,
        request: HttpRequest | None = None,
    ) -> SafeString:
        return self.render_children(
            self.get_slot(name),
            request=request,
        )

    def render_template(
        self,
        template: str,
        context: dict[str, Any],
        request: HttpRequest | None = None,
    ) -> SafeString:
        return mark_safe(
            render_to_string(template, context, request=request)
        )

    def render_content(self, content: Any) -> SafeString:
        if isinstance(content, SafeString):
            return content

        return mark_safe(str(content))

    def render(self, request: HttpRequest | None = None) -> SafeString:
        if request is not None:
            self.set_request(request)

        actual_request = request or self.request

        content = self.get_content()

        if content is not None:
            return self.render_content(content)

        template = self.get_template()

        if template:
            return self.render_template(
                template,
                self.get_context(),
                request=actual_request,
            )

        if self.children:
            return self.render_children(request=actual_request)

        raise ValueError(
            f"{type(self).__name__} has no content, "
            "children, or template."
        )

    def __html__(self) -> SafeString:
        return self.render()

    def __str__(self) -> str:
        return str(self.render())
