from __future__ import annotations

from typing import TypeVar

from .directives import AttributeDirective


DirectiveType = TypeVar(
    "DirectiveType",
    bound=AttributeDirective,
)


class DirectiveRegistry:
    """
    Registry for HTML attribute directives.

    The registry is intentionally unaware of any application
    or framework-specific directive implementation.
    """

    def __init__(self):
        self._directives: dict[
            str,
            AttributeDirective,
        ] = {}

    def register(
        self,
        directive: (
            AttributeDirective
            | type[DirectiveType]
        ),
        *,
        replace: bool = False,
    ) -> None:

        if isinstance(directive, type):
            directive = directive()

        name = getattr(directive, "name", None)

        if not isinstance(name, str) or not name:
            raise ValueError(
                "A directive must define a non-empty name."
            )

        if (
            name in self._directives
            and not replace
        ):
            raise ValueError(
                f"Directive already registered: {name}"
            )

        self._directives[name] = directive

    def get(
        self,
        name: str,
    ) -> AttributeDirective | None:

        return self._directives.get(name)

    def unregister(self, name: str) -> None:

        self._directives.pop(name, None)

    def contains(self, name: str) -> bool:

        return name in self._directives

    def __contains__(self, name: str) -> bool:

        return self.contains(name)

    def __len__(self) -> int:

        return len(self._directives)