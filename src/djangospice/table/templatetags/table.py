from __future__ import annotations

from django import template
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import SafeString

from djangospice.table.apps import namespace


register = template.Library()


TABLE_CSS = f"{namespace}/css/table.css"
DATATABLE_JS = f"{namespace}/js/datatable.js"
CONTEXTMENU_JS = f"{namespace}/js/contextmenu.js"


def _table_css() -> str:
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static(TABLE_CSS),
    )


def _table_js() -> str:
    return format_html(
        '<script src="{}" defer></script>',
        static(DATATABLE_JS),
    )


def _contextmenu_js() -> str:
    return format_html(
        '<script src="{}" defer></script>',
        static(CONTEXTMENU_JS),
    )


@register.simple_tag
def table_css() -> str:
    """Render the DjangoSpice Table stylesheet."""
    return _table_css()


@register.simple_tag
def table_js() -> str:
    """Render the DjangoSpice DataTable JavaScript."""
    return _datatable_js()


@register.simple_tag
def contextmenu_js() -> str:
    """Render the DjangoSpice Table context-menu JavaScript."""
    return _contextmenu_js()



@register.simple_tag
def table_assets() -> SafeString:
    """Render all Lookup assets."""
    return format_html("{}\n{}", _table_css(), _table_js())
