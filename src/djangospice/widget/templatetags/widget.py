from __future__ import annotations

from typing import Any
from urllib.parse import urlencode
from django import template
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe

from djangospice.widget.exceptions import WidgetNotVisible
from djangospice.widget.registry import WidgetRegistry
from djangospice.widget.renderer import render
from djangospice.widget.widget import Widget


register = template.Library()


@register.simple_tag(takes_context=True)
def render_widget(context: template.Context, identifier: str, **kwargs: Any) -> SafeString:
    """
    Template tag to dynamically render a registered widget.
    
    Usage:
        {% render_widget "analytics:monthly_chart" period="year" %}
    """
    request = context.get("request")

  
    try:
        widget_class = WidgetRegistry.get(identifier)
    except KeyError as e:
        return mark_safe(str(e))

   
    try:
        widget = widget_class(request=request, **kwargs)
        return render(widget)
    except WidgetNotVisible:
        return mark_safe("")


@register.simple_tag(takes_context=True)
def render_children(context: template.Context, widget: Widget) -> SafeString:
    """
    Render all direct children of a widget.

    Example:

        {% render_children widget %}
    """
    rendered = []

    for child in widget.get_children():
        rendered.append(render(child))

    return mark_safe("".join(rendered))

@register.simple_tag(takes_context=True)
def render_slot(context: template.Context, widget: Widget, name: str) -> SafeString:
    """
    Render all widgets assigned to a named slot.

    Example:

        {% render_slot widget "header" %}
    """
    rendered = []

    for child in widget.get_slot(name):
        rendered.append(render(child))

    return mark_safe("".join(rendered))


@register.simple_tag
def widget_url(url, **kwargs):
    """
    Build a widget action URL with query parameters.

    Usage:
        {% widget_url widget.mark_as_read id=notification.id %}
    """
    if not url:
        return ""

    if not kwargs:
        return url

    query = urlencode(kwargs)

    separator = "&" if "?" in url else "?"

    return format_html("{}{}{}", url, separator, query)