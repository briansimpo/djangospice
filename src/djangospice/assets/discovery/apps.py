from pathlib import Path, PurePosixPath
from django.apps import apps
from django.contrib.staticfiles import finders
from djangospice.assets.conf import get_setting

ASSET_TYPES = {
    "js": "js",
    "javascript": "js",
    "css": "css",
    "stylesheet": "css",
    "styles": "css",
}


def is_djangospice_app(config) -> bool:
        """
        Identify Djangospice applications and extensions.
        """
        return getattr(config, "djangospice_app", False) is True


def _find(relative_path):
    matches = finders.find(relative_path, all=True)
    if not matches:
        return None
    source = matches[0]
    if isinstance(source, (list, tuple)):
        source = source[0]
    return str(Path(source).resolve())


def discover_assets():
    """Return installed Djangospice apps and their optional JS/CSS entry points."""
    result = []
    for app_config in apps.get_app_configs():
        if not is_djangospice_app(app_config):
            continue
        label = app_config.label
        js_path = _find(f"{label}/{get_setting('JS_ENTRYPOINT')}")
        css_path = _find(f"{label}/{get_setting('CSS_ENTRYPOINT')}")
        if js_path or css_path:
            result.append({"app": label, "js": js_path, "css": css_path})
    return result


def get_entrypoint(app_config, asset_type):
    """
    Resolve an app's asset entry point.

    Convention:

        static/<app_label>/js/index.js
        static/<app_label>/css/index.css
    """

    extension = ASSET_TYPES[asset_type]

    entrypoint = get_setting(
        "JS_ENTRYPOINT"
    ) if extension == "js" else get_setting(
        "CSS_ENTRYPOINT"
    )

    relative_path = PurePosixPath(
        app_config.label,
        entrypoint,
    ).as_posix()

    matches = finders.find(
        relative_path,
        all=True,
    )

    if not matches:
        return None

    # Resolve duplicate static paths deterministically.
    resolved = []

    for match in matches:
        if isinstance(match, (list, tuple)):
            resolved.extend(match)
        else:
            resolved.append(match)

    resolved = sorted(
        {
            str(path)
            for path in resolved
        }
    )

    return resolved[0] if resolved else None


def discover_entrypoints(asset_type="js", *, app_label=None, include_non_djangospice=False):
    """
    Discover asset entry points from installed Django applications.

    Args:
        asset_type:
            js, javascript, css, stylesheet, or styles.

        app_label:
            Optionally restrict discovery to one installed Django app.

        include_non_djangospice:
            Include ordinary Django apps when True.

    Returns:
        list[tuple[str, str]]:
            [(app_label, absolute_entrypoint_path), ...]
    """

    try:
        asset_type = ASSET_TYPES[asset_type.lower()]
    except (AttributeError, KeyError):
        raise ValueError(
            "Unsupported asset type. "
            "Expected js, javascript, css, stylesheet, or styles."
        )

    discovered = []

    app_configs = sorted(
        apps.get_app_configs(),
        key=lambda config: config.label,
    )

    for app_config in app_configs:

        if app_label and app_config.label != app_label:
            continue

        if (
            not include_non_djangospice
            and not is_djangospice_app(app_config)
        ):
            continue

        entrypoint = get_entrypoint(
            app_config,
            asset_type,
        )

        if entrypoint is None:
            continue

        discovered.append(
            (
                app_config.label,
                entrypoint,
            )
        )

    return discovered


def watch_roots():
    roots = set()
    for item in discover_assets():
        for kind in ("js", "css"):
            source = item[kind]
            if source:
                # Watch the app's static/<app_label> tree, not only its entry file.
                roots.add(str(Path(source).parents[1]))
    return sorted(roots)
