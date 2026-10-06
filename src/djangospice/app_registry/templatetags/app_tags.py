from __future__ import annotations

from django import template
from django.urls import reverse
from django.apps import apps

from djangospice.urls import safe_reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def app_url(context,view_name: str,*args,**kwargs):
    request = context.get("request")

    if request is None:
        return safe_reverse(
            view_name,
            args=args,
            kwargs=kwargs,
        )

    resolver_match = getattr(request, "resolver_match", None)

    if resolver_match is None:
        return safe_reverse(
            view_name,
            args=args,
            kwargs=kwargs,
        )

    app_name = resolver_match.app_name

    if not app_name:
        return safe_reverse(
            view_name,
            args=args,
            kwargs=kwargs,
        )

    try:
        app_config = apps.get_app_config(app_name)
    except LookupError:
        return safe_reverse(
            view_name,
            args=args,
            kwargs=kwargs,
        )

    namespace = getattr(
        app_config,
        "namespace",
        None,
    ) or app_config.label

    return safe_reverse(
        view_name,
        namespace,
        args=args,
        kwargs=kwargs,
    )


@register.simple_tag(takes_context=True)
def app_filter_url(context) -> str:
    """
    Return the current view URL without query parameters.

    Preserves:
    - URL namespaces
    - URL name
    - positional URL arguments
    - keyword URL arguments

    Query-string parameters are intentionally excluded.
    """
    request = context.get("request")

    if request is None:
        return ""

    resolver_match = getattr(request, "resolver_match", None)

    if resolver_match is None:
        return ""

    url_name = resolver_match.url_name

    if not url_name:
        return ""

    namespaces = resolver_match.namespaces

    if namespaces:
        full_name = ":".join((*namespaces, url_name))
    else:
        full_name = url_name

    return reverse(
        full_name,
        args=resolver_match.args or None,
        kwargs=resolver_match.kwargs or None,
    )