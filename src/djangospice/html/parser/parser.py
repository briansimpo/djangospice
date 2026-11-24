from __future__ import annotations

from html import unescape
from html.parser import HTMLParser as StdlibHTMLParser

from .nodes import (
    CommentNode,
    DeclarationNode,
    DocumentNode,
    ElementNode,
    TextNode,
    VOID_ELEMENTS,
    RAW_TEXT_ELEMENTS,
)


class FragmentParser(StdlibHTMLParser):
    """
    Parse an HTML fragment into a lightweight node tree.

    This parser is generic. It knows nothing about LiveComponent,
    HTMX directives or Djangospice application behavior.
    """

    def __init__(self):
        super().__init__(convert_charrefs=False)

        self.document = DocumentNode()
        self._elements: list[ElementNode] = []

    @property
    def _children(self):
        if self._elements:
            return self._elements[-1].children

        return self.document.children

    def parse(self, markup: str) -> DocumentNode:

        self.feed(markup)
        self.close()

        return self.document

    def handle_starttag(self, tag, attrs):

        node = ElementNode(
            tag=tag,
            attributes=dict(attrs),
        )

        self._children.append(node)

        if tag.lower() not in VOID_ELEMENTS:
            self._elements.append(node)

    def handle_startendtag(self, tag, attrs):

        node = ElementNode(
            tag=tag,
            attributes=dict(attrs),
            self_closing=True,
        )

        self._children.append(node)

    def handle_endtag(self, tag):

        tag = tag.lower()

        for index in range(
            len(self._elements) - 1,
            -1,
            -1,
        ):
            if self._elements[index].tag.lower() == tag:
                del self._elements[index:]
                return

    def handle_data(self, data):

        if not data:
            return

        raw = False

        if self._elements:
            raw = (
                self._elements[-1].tag.lower()
                in RAW_TEXT_ELEMENTS
            )

        self._children.append(
            TextNode(
                value=data,
                raw=raw,
            )
        )

    def handle_entityref(self, name):

        self._children.append(
            TextNode(
                value=unescape(f"&{name};")
            )
        )

    def handle_charref(self, name):

        self._children.append(
            TextNode(
                value=unescape(f"&#{name};")
            )
        )

    def handle_comment(self, data):

        self._children.append(
            CommentNode(data)
        )

    def handle_decl(self, decl):

        self._children.append(
            DeclarationNode(decl)
        )

    def handle_pi(self, data):

        self._children.append(
            DeclarationNode(
                value=data,
                prefix="<?",
                suffix=">",
            )
        )

    def unknown_decl(self, data):

        self._children.append(
            DeclarationNode(
                value=data,
                prefix="<![",
                suffix="]]>",
            )
        )