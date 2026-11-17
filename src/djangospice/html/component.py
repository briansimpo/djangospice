
from __future__ import annotations

from typing import Any, ClassVar, Dict, Iterable, List

from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.html import conditional_escape
from django.utils.safestring import SafeString, mark_safe

from djangospice.html.slots import Slots

from .attributes import HTMLAttributeRenderer, HTMXAttributes


class Component:
    """
    Base class for composable UI components.

    Provides component lifecycle, composition, attributes,
    request propagation, context and rendering.
    """

    template_name: ClassVar[str | None] = None
    
    # Used as app root
    app_view: ClassVar[str] = "spice-app"


    def __init__(self, *args, **kwargs: Any) -> None:
        self.request: HttpRequest | None = kwargs.pop("request", None)
        self.parent = kwargs.pop("parent", None)

        # Rendering configuration
        self.template_name = kwargs.pop(
            "template_name",
            type(self).template_name,
        )

        self.context: Dict = kwargs.pop("context", {}) or {}

        # HTML configuration
        self.attributes: Dict = kwargs.pop("attributes", {}) or {}
        self.htmx: HTMXAttributes = (
            kwargs.pop("htmx", None) or HTMXAttributes()
        )
        self.css_class = kwargs.pop("css_class", None)

        # Composition
        self.children: List = []
        self._slots: Dict[str, List] = {}
        self.slots = Slots(self)

        # Extract initial slots BEFORE preserving remaining kwargs.
        initial_slots = kwargs.pop("slots", {}) or {}

        # Preserve remaining component properties.
        self.kwargs = kwargs

        # Initialize ordinary children.
        self.add_children(*args)

        # Initialize named slots through the public API.
        for name, components in initial_slots.items():
            if isinstance(components, (list, tuple)):
                self.set_slot(name, *components)
            else:
                self.set_slot(name, components)
        super().__init__()

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

        name = (
            self.attributes.get("name")
            or type(self).__name__.lower()
        )

        return str(name)

    @property
    def attrs(self) -> SafeString:
        return mark_safe(
            HTMLAttributeRenderer.render(
                self.get_html_attributes()
            )
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
        self._slots.setdefault(name, []).append(child)
        return child


    def add_to_slots(self, **slots: Any) -> None:
        for name, value in slots.items():
            if isinstance(value, (list, tuple)):
                self.set_slot(name, *value)
            else:
                self.set_slot(name, value)


    def get_slot(self, name: str) -> tuple[Any, ...]:
        return tuple(self._slots.get(name, ()))


    def has_slot(self, name: str) -> bool:
        return bool(self._slots.get(name))


    def remove_from_slot(self, name: str, child: Any) -> None:
        children = self._slots.get(name)

        if not children or child not in children:
            return

        children.remove(child)

        if isinstance(child, Component) and child.parent is self:
            child.parent = None

        if not children:
            self._slots.pop(name, None)


    def clear_slot(self, name: str) -> None:
        for child in self._slots.get(name, ()):
            if isinstance(child, Component) and child.parent is self:
                child.parent = None

        self._slots.pop(name, None)


    def clear_slots(self) -> None:
        for name in tuple(self._slots):
            self.clear_slot(name)

    # --------------------------------------------------------
    # Parent and request
    # --------------------------------------------------------

    def _attach(self, child: Any) -> None:
        if not isinstance(child, Component):
            return

        if child is self:
            raise ValueError(
                "A component cannot contain itself."
            )

        parent = self

        while parent is not None:
            if parent is child:
                raise ValueError(
                    "Circular component hierarchy detected."
                )

            parent = parent.parent

        if child.parent is not None:
            child.parent._detach(child)

        child.parent = self

        if child.request is None:
            child.set_request(self.request)

    def _detach(self, child: Component) -> None:
        if child in self.children:
            self.children.remove(child)

        for name, children in tuple(self._slots.items()):
            if child in children:
                children.remove(child)

            if not children:
                self._slots.pop(name, None)

        if child.parent is self:
            child.parent = None

    def set_request(
        self,
        request: HttpRequest | None,
    ) -> None:
        self.request = request

        for child in self._iter_components():
            if child.request is None:
                child.set_request(request)

    def _iter_components(self):
        seen = set()

        for child in self.children:
            if isinstance(child, Component) and id(child) not in seen:
                seen.add(id(child))
                yield child

        for children in self._slots.values():
            for child in children:
                if isinstance(child, Component) and id(child) not in seen:
                    seen.add(id(child))
                    yield child

    # --------------------------------------------------------
    # Content and context
    # --------------------------------------------------------

    def get_content(self) -> Any:
        return None

    def get_template(self) -> str | None:
        return self.template_name

    def get_context(self):
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

    def render_child(self, child: Any) -> SafeString:
        if child is None:
            return mark_safe("")

        if isinstance(child, Component):
            return child.render_to_string()

        if isinstance(child, (list, tuple)):
            return self.render_children(child)

        return conditional_escape(child)

    def render_children(
        self,
        children: Iterable[Any] | None = None,
    ) -> SafeString:
        children = (
            self.get_children()
            if children is None
            else children
        )

        return mark_safe(
            "".join(
                str(self.render_child(child))
                for child in children
            )
        )

    def render_slot(self, name: str) -> SafeString:
        return self.render_children(
            self.get_slot(name)
        )

    def render_slots(self) -> SafeString:
        return mark_safe(
            "".join(
                str(self.render_slot(name))
                for name in self._slots
            )
        )

    def render_template(
        self,
        template: str,
        context: dict[str, Any],
    ) -> SafeString:
        return mark_safe(
            render_to_string(
                template,
                context,
                request=self.request,
            )
        )

    def render_content(self, content: Any) -> SafeString:
        if isinstance(content, SafeString):
            return content

        return mark_safe(str(content))

    def render_to_string(self) -> SafeString:
        content = self.get_content()

        if content is not None:
            return self.render_content(content)

        template = self.get_template()

        if template:
            return self.render_template(
                template,
                self.get_context(),
            )

        if self.children:
            return self.render_children()

        if self.slots:
            return self.render_slots()

        raise ValueError(
            f"{type(self).__name__} has no content, "
            "children, slots, or template."
        )

    def __html__(self) -> SafeString:
        return self.render_to_string()

    def __str__(self) -> str:
        return str(self.render_to_string())
