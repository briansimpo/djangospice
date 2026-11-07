from __future__ import annotations

from .registry import WidgetRegistry


def widget(widget_klass):
    WidgetRegistry.register(widget_klass)
    return widget_klass
