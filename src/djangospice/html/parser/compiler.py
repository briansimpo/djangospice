from __future__ import annotations

from typing import Any

from .nodes import (
    DocumentNode,
    ElementNode,
    render_document,
)
from .parser import FragmentParser
from .registry import DirectiveRegistry


class MarkupCompiler:
    """
    Generic HTML compiler.

    Strict prefixes are optional and generic. They allow a
    compiler user to reject attributes that belong to an
    unregistered directive namespace.
    """

    def __init__(
        self,
        registry: DirectiveRegistry,
        context: Any = None,
        strict_prefixes: tuple[str, ...] = (),
    ):
        self.registry = registry
        self.context = context
        self.strict_prefixes = strict_prefixes

    def compile(self, markup: str) -> str:

        document = FragmentParser().parse(markup)

        self.compile_document(document)

        return render_document(document)

    def compile_document(
        self,
        document: DocumentNode,
    ) -> DocumentNode:

        self._compile_nodes(document.children)

        return document

    def _compile_nodes(self, nodes) -> None:

        for node in nodes:

            if not isinstance(node, ElementNode):
                continue

            directives = [
                (name, value)
                for name, value in list(
                    node.attributes.items()
                )
                if self.registry.contains(name)
            ]

            for name, value in directives:

                directive = self.registry.get(name)

                if directive is not None:
                    directive.compile(
                        node=node,
                        value=value,
                        context=self.context,
                    )

            self._validate_attributes(node)

            self._compile_nodes(node.children)

    def _validate_attributes(
        self,
        node: ElementNode,
    ) -> None:

        for name in node.attributes:

            for prefix in self.strict_prefixes:

                if (
                    name.startswith(prefix)
                    and not self.registry.contains(name)
                ):
                    raise ValueError(
                        f"Unknown markup directive: {name}"
                    )