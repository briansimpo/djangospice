from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from typing import TypeAlias


VOID_ELEMENTS = {
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
}

RAW_TEXT_ELEMENTS = {
    "script",
    "style",
}


@dataclass(slots=True)
class TextNode:
    value: str
    raw: bool = False


@dataclass(slots=True)
class CommentNode:
    value: str


@dataclass(slots=True)
class DeclarationNode:
    value: str
    prefix: str = "<!"
    suffix: str = ">"


@dataclass(slots=True)
class ElementNode:
    tag: str
    attributes: dict[str, str | None] = field(
        default_factory=dict
    )
    children: list[Node] = field(default_factory=list)
    self_closing: bool = False


Node: TypeAlias = (
    TextNode
    | CommentNode
    | DeclarationNode
    | ElementNode
)


@dataclass(slots=True)
class DocumentNode:
    children: list[Node] = field(default_factory=list)


def render_node(node: Node) -> str:

    if isinstance(node, TextNode):
        if node.raw:
            return node.value

        return escape(node.value, quote=False)

    if isinstance(node, CommentNode):
        return f"<!--{node.value}-->"

    if isinstance(node, DeclarationNode):
        return (
            f"{node.prefix}"
            f"{node.value}"
            f"{node.suffix}"
        )

    if isinstance(node, ElementNode):
        attributes = render_attributes(node.attributes)

        opening = (
            f"<{node.tag}"
            f"{' ' + attributes if attributes else ''}"
        )

        if node.tag.lower() in VOID_ELEMENTS:
            return f"{opening}>"

        if node.self_closing:
            return f"{opening} />"

        content = "".join(
            render_node(child)
            for child in node.children
        )

        return (
            f"{opening}>"
            f"{content}"
            f"</{node.tag}>"
        )

    raise TypeError(
        f"Unsupported HTML node: {type(node).__name__}"
    )


def render_attributes(
    attributes: dict[str, str | None],
) -> str:

    parts: list[str] = []

    for name, value in attributes.items():

        safe_name = escape(str(name), quote=True)

        # Boolean HTML attribute.
        if value is None:
            parts.append(safe_name)
            continue

        safe_value = escape(str(value), quote=True)

        parts.append(
            f'{safe_name}="{safe_value}"'
        )

    return " ".join(parts)


def render_document(document: DocumentNode) -> str:

    return "".join(
        render_node(node)
        for node in document.children
    )