from typing import Any

from django import template
from django.utils.safestring import SafeString

from djangospice.widgets.exceptions import WidgetNotVisible
from djangospice.widgets.registry import WidgetRegistry
from djangospice.widgets.renderer import WidgetRenderer

register = template.Library()


@register.simple_tag(takes_context=True)
def render_widget(context: template.Context, widget_key: str, **kwargs: Any) -> SafeString:
    request = context.get("request")

    try:
        widget_class = WidgetRegistry.get(widget_key)
    except KeyError:
        return SafeString("")

    widget = widget_class(request=request, **kwargs)

    try:
        return WidgetRenderer(widget).render()
    except WidgetNotVisible:
        return SafeString("")