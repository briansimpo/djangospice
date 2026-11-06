from __future__ import annotations

from .registry import WidgetRegistry


def widget(widget_class):
    """
    Register a Widget class explicitly.
    """
    WidgetRegistry.register(widget_class)
    return widget_class
