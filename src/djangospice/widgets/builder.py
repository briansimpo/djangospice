from __future__ import annotations

from typing import Any
from django.template.loader import render_to_string
from django.utils.safestring import SafeString, mark_safe

from .assets import AssetRegistry
from .exceptions import WidgetError
from .widget import Widget


class WidgetBuilder:
    """
    Builds widget content into a rendered HTML string with support for 
    flexible content types returned by the widget.
    """

    def __init__(self, widget: Widget, registry: AssetRegistry = None) -> None:
        self.widget = widget
        self.registry = registry

    def build(self) -> str:
        # 1. Render the HTML
        content = self.widget.get_content()
        
        if isinstance(content, str):
            rendered_html = content
        else:
            context = self.widget.get_context()
            if isinstance(content, dict):
                context.update(content)
            rendered_html = self._render(context)

        # 2. POST-RENDERING HOOK
        # Automatically collect assets defined by the widget
        if self.registry and hasattr(self.widget, "get_assets"):
            assets = self.widget.get_assets()
            self.registry.add(
                js=assets.get("js"), 
                css=assets.get("css")
            )

        return mark_safe(rendered_html)

    def _render(self, context: dict[str, Any]) -> SafeString:
        """
        Render the widget's template using the provided context.
        """
        try:
            template = self.widget.get_template()
        except ValueError as e:
            # Unify exceptions: Catch Widget's ValueError and raise as Configuration Error
            raise WidgetError(str(e)) from e

        if not template:
            raise WidgetError(
                f"Widget '{self.widget.name}' (`{self.widget.__class__.__name__}`) "
                "does not define a template."
            )

        rendered_html = render_to_string(
            template_name=template,
            context=context,
            request=self.widget.request,
        )
        
        return mark_safe(rendered_html)