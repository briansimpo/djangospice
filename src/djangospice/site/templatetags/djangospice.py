
import json
from django import template
from django.apps import apps
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import NoReverseMatch
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.templatetags.static import static
from djangospice.utils import safe_reverse
from djangospice.assets.manager import AssetManager
from djangospice.assets.utils import asset_url
from djangospice.assets.compiler.manifest import read_manifest
from djangospice.assets.conf import get_build_root, get_setting


register = template.Library()


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
def djangospice_assets(asset_type=None):
    """
    Automatically render CSS and JavaScript assets
    from all installed Djangospice apps and extensions.

    Usage:
        {% djangospice_assets %}

    Optional:
        {% djangospice_assets "css" %}
        {% djangospice_assets "js" %}
    """
    if asset_type not in (None, "css", "js"):
        raise ValueError(
            "asset_type must be 'css', 'js' or None."
        )

    app_assets = AssetManager.get_apps_assets()

    css_files = []
    js_files = []

    for assets in app_assets.values():
        if asset_type in (None, "css"):
            css_files.extend(assets["css"])

        if asset_type in (None, "js"):
            js_files.extend(assets["js"])

    # Avoid duplicates while preserving discovery order.
    css_files = list(dict.fromkeys(css_files))
    js_files = list(dict.fromkeys(js_files))

    css_html = format_html_join(
        "\n",
        '<link rel="stylesheet" href="{}">',
        ((static(asset),) for asset in css_files),
    )

    js_html = format_html_join(
        "\n",
        '<script src="{}" defer></script>',
        ((static(asset),) for asset in js_files),
    )

    return format_html("{}\n{}", css_html, js_html)


@register.simple_tag
def djangospice_bundle():
    manifest_path = get_build_root() / get_setting("OUTPUT_DIR") / "manifest.json"
    manifest = read_manifest(manifest_path)

    if not manifest:
        if settings.DEBUG:
            raise RuntimeError("Djangospice assets have not been built. Run python manage.py djangospice_assets build.")
        return ""

    tags = []

    css = manifest.get("css", {}).get("main")
    js = manifest.get("js", {}).get("main")

    if css:
        tags.append(format_html('<link rel="stylesheet" href="{}">', asset_url(css)))

    if js:
        tags.append(format_html('<script src="{}" defer></script>', asset_url(js)))

    return format_html_join(
        "\n",
        "{}",
        ((tag,) for tag in tags),
    )