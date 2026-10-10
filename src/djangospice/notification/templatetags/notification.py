from __future__ import annotations

import json

from django import template
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from djangospice.routing import safe_reverse

from djangospice.notification.apps import namespace


register = template.Library()

INDEX_JS = f"{namespace}/js/index.js"


def notification_js() -> str:
    return f'<script src="{static(INDEX_JS)}" defer></script>'


@register.simple_tag
def notification_endpoints() -> str:
    """
    Return notification API endpoints as JSON.
    """

    endpoints = {
        "unreadList": safe_reverse(
            "api-unread",
            namespace,
        ),
        "allList": safe_reverse(
            "api-all",
            namespace,
        ),
        "unreadCount": safe_reverse(
            "api-unread-count",
            namespace,
        ),
        "allCount": safe_reverse(
            "api-all-count",
            namespace,
        ),
        "markAllRead": safe_reverse(
            "api-mark-all-read",
            namespace,
        ),
    }

    return mark_safe(
        json.dumps(endpoints)
    )