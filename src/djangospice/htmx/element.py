
from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any, ClassVar

from django.utils.html import conditional_escape
from django.utils.safestring import SafeData, mark_safe

from .component import Component


class HTMLElement(Component):
    """
    Base class for composable HTML elements.

    Supports:
    - positional child elements and text
    - arbitrary HTML attributes
    - normalized Python attribute names
    - HTMX attributes
    - nested components
    - safe HTML rendering
    - HTML void elements
    """

    tag_name: ClassVar[str] = ""

    void_elements: ClassVar[frozenset[str]] = frozenset({
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    })

    _tag_pattern = re.compile(r"^[a-zA-Z][a-zA-Z0-9:-]*$")

    def __init__(
        self,
        *children: Any,
        tag_name: str | None = None,
        request=None,
        parent: Component | None = None,
        children_list: Iterable[Any] | None = None,
        slots: dict[str, list[Component]] | None = None,
        context: dict[str, Any] | None = None,
        attributes: dict[str, Any] | None = None,
        htmx=None,
        class_name: str = "",
        **html_attributes: Any,
    ) -> None:
        tag = tag_name or self.tag_name

        if not tag or not self._tag_pattern.fullmatch(tag):
            raise ValueError(f"Invalid HTML tag name: {tag!r}")

        self.tag_name = tag.lower()

        merged_attributes = self.normalize_attributes(
            {
                **(attributes or {}),
                **html_attributes,
            }
        )

        if class_name:
            existing = merged_attributes.get("class", "")
            merged_attributes["class"] = " ".join(
                value for value in (existing, class_name) if value
            )

        all_children = (*children, *(children_list or ()))

        if self.is_void and all_children:
            raise ValueError(
                f"The <{self.tag_name}> element cannot have children."
            )

        super().__init__(
            *all_children,
            request=request,
            parent=parent,
            slots=slots,
            context=context,
            attributes=merged_attributes,
            htmx=htmx,
        )

    # ------------------------------------------------------------------
    # Attributes
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_attribute_name(name: str) -> str:
        """
        Convert Python-friendly attribute names to HTML names.

        Examples:
            class_name   -> class
            for_         -> for
            data_test_id -> data-test-id
            hx_post      -> hx-post
        """
        if name == "class_name":
            return "class"

        if name.endswith("_"):
            name = name[:-1]

        return name.replace("_", "-")


    @classmethod
    def normalize_attributes(
        cls,
        attributes: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            cls.normalize_attribute_name(name): value
            for name, value in attributes.items()
        }

    @property
    def id(self) -> str | None:
        """
        HTML elements only receive an ID when explicitly provided.
        """
        return self.attributes.get("id")

    @property
    def is_void(self) -> bool:
        return self.tag_name in self.void_elements

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_child(self, child: Any) -> str:
        """
        Render a child while preserving HTML safety.
        """
        if child is None or isinstance(child, bool):
            return ""

        if isinstance(child, Component):
            return str(child.render(request=self.request))

        if isinstance(child, SafeData):
            return str(child)

        if isinstance(child, (list, tuple)):
            return "".join(
                self.render_child(item)
                for item in child
            )

        return str(conditional_escape(child))

    def render_children(self) -> str:
        return "".join(
            self.render_child(child)
            for child in self.get_children()
        )

    def get_content(self) -> str:
        """
        Render the complete HTML element.
        """
        attributes = str(self.attr)
        opening_tag = f"<{self.tag_name}"

        if attributes:
            opening_tag += f" {attributes}"

        opening_tag += ">"

        if self.is_void:
            return mark_safe(opening_tag)

        content = self.render_children()
        closing_tag = f"</{self.tag_name}>"

        return mark_safe(
            f"{opening_tag}{content}{closing_tag}"
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} tag={self.tag_name!r}>"
