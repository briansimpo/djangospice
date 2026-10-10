
from __future__ import annotations

from django import template
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import SafeString

from djangospice.lookup.apps import namespace

register = template.Library()


LOOKUP_CSS = f"{namespace}/css/lookup.css"
LOOKUP_JS = f"{namespace}/js/lookup.js"


def _lookup_css() -> SafeString:
    """Render the Lookup stylesheet."""
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static(LOOKUP_CSS),
    )


def _lookup_js() -> SafeString:
    """Render the Lookup JavaScript."""
    return format_html(
        '<script src="{}" defer></script>',
        static(LOOKUP_JS),
    )


@register.simple_tag
def lookup_css() -> SafeString:
    """Render the Lookup stylesheet."""
    return _lookup_css()


@register.simple_tag
def lookup_js() -> SafeString:
    """Render the Lookup JavaScript."""
    return _lookup_js()


@register.simple_tag
def lookup_assets() -> SafeString:
    """Render all Lookup assets."""
    return format_html("{}\n{}", _lookup_css(), _lookup_js())
