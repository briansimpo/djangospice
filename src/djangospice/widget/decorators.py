from __future__ import annotations

from djangospice.exec.registry import Registry

def widget(widget_klass):
    Registry.register(widget_klass)
    return widget_klass
