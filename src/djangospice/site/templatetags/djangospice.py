
import json
from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import NoReverseMatch
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.templatetags.static import static
from django.apps import apps
from djangospice.utils import safe_reverse
from djangospice.site.assets import get_assets, get_asset_path


register = template.Library()


def _render_styles(paths):
    return format_html_join(
        "\n",
        '<link rel="stylesheet" href="{}">',
        ((static(path),) for path in paths),
    )


def _render_scripts(paths):
    return format_html_join(
        "\n",
        '<script type="module" src="{}"></script>',
        ((static(path),) for path in paths),
    )


@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, "")


@register.filter
def get_item(data: dict, key: str):
    return data.get(key, None)


@register.filter
def object_url(object, url_name):
    try:
        return safe_reverse(url_name, args=[object.pk])
    except NoReverseMatch:
        return "#"


@register.filter
def jsonify(obj):
    """
    Converts model or dict to JSON safely.
    """
    if hasattr(obj, "to_dict"):
        obj = obj.to_dict()

    return json.dumps(obj, cls=DjangoJSONEncoder)


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
def filter_url(context) -> str:
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


@register.simple_tag
def djangospice_asset(module, asset_type="js", name=None):
    """Return an asset URL when its path can be resolved."""
    path = get_asset_path(module, asset_type, name)

    return static(path) if path else ""


@register.simple_tag
def djangospice_assets(module):
    """Render all discovered CSS and JavaScript assets."""
    assets = get_assets(module)
    return format_html(
        "{}\n{}",
        _render_styles(assets["css"]),
        _render_scripts(assets["js"]),
    )


@register.simple_tag
def djangospice_style(module, name=None):
    """Render discovered stylesheets."""
    paths = get_assets(module, "css")

    if name:
        paths = [
            path for path in paths
            if path.rsplit("/", 1)[-1] == name
        ]

    return _render_styles(paths)


@register.simple_tag
def djangospice_script(module, name=None):
    """Render discovered JavaScript modules."""
    paths = get_assets(module, "js")

    if name:
        paths = [
            path for path in paths
            if path.rsplit("/", 1)[-1] == name
        ]

    return _render_scripts(paths)
