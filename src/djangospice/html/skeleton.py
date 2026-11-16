from __future__ import annotations

from typing import ClassVar

from .component import Component


class Skeleton(Component):
    """
    Generic loading placeholder.

    Supports dimensions, variants, animation, and composition.
    """

    template_name = "html/skeleton.html"

    VARIANTS: ClassVar[dict] = {
        "default": {
            "width": "100%",
            "height": "16px",
            "radius": "rounded-md",
        },
        "text": {
            "width": "100%",
            "height": "14px",
            "radius": "rounded",
        },
        "title": {
            "width": "180px",
            "height": "24px",
            "radius": "rounded-md",
        },
        "avatar": {
            "width": "40px",
            "height": "40px",
            "radius": "rounded-full",
        },
        "image": {
            "width": "100%",
            "height": "180px",
            "radius": "rounded-lg",
        },
        "button": {
            "width": "100px",
            "height": "36px",
            "radius": "rounded-md",
        },
    }

    def __init__(
        self,
        width: str | int | None = None,
        height: str | int | None = None,
        variant: str = "default",
        radius: str | None = None,
        animate: bool = True,
        template_name: str| None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.width = width
        self.height = height
        self.variant = variant
        self.radius = radius
        self.animate = animate
        if template_name is not None:
            self.template_name = template_name

    @staticmethod
    def _size(value):
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return f"{value}px"

        return str(value)

    def get_context(self):
        context = super().get_context()

        variant = self.VARIANTS.get(
            self.variant,
            self.VARIANTS["default"],
        )

        width = self._size(self.width or variant["width"])
        height = self._size(self.height or variant["height"])
        radius = self.radius or variant["radius"]

        classes = [
            "skeleton",
            f"skeleton--{self.variant}",
            f"skeleton--{radius}",
        ]

        if self.animate:
            classes.append("skeleton--animated")

        if self.css_class:
            classes.append(self.css_class)

        styles = []

        if width:
            styles.append(f"width: {width}")

        if height:
            styles.append(f"height: {height}")

        context.update({
            "skeleton_classes": " ".join(classes),
            "skeleton_style": "; ".join(styles),
            "skeleton_animated": self.animate,
        })

        return context