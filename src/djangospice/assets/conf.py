from pathlib import Path

from django.conf import settings

DEFAULTS = {
    "JS_ENTRYPOINT": "js/index.js",
    "CSS_ENTRYPOINT": "css/index.css",

    "JS_OUTPUT_NAME": "djangospice.js",
    "CSS_OUTPUT_NAME": "djangospice.css",
    "ESBUILD_BINARY": "esbuild",
    "TARGET": "es2020",
    "FORMAT": "iife",
    "PLATFORM": "browser",
    "MINIFY": not settings.DEBUG,
    "SOURCEMAP": bool(settings.DEBUG),
    "GLOBAL_NAME": "Djangospice",

    "OUTPUT_DIR": "djangospice",
    "BUILD_DIR": settings.BASE_DIR / "assets",

    "HMR": bool(settings.DEBUG),
    "HMR_HOST": "",
    "HMR_BIND_HOST": "127.0.0.1",
    "HMR_PORT": 8765,
    "HMR_PATH": "/__djangospice_hmr__",
    "WATCH_DEBOUNCE": 300,
}


def get_setting(name):
    user_settings = getattr(settings, "DJANGOSPICE_ASSETS", {})
    if not isinstance(user_settings, dict):
        raise TypeError("DJANGOSPICE_ASSETS must be a dictionary.")
    return user_settings.get(name, DEFAULTS[name])


def get_build_root():
    configured = get_setting("BUILD_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    static_root = getattr(settings, "STATIC_ROOT", None)
    if static_root:
        return Path(static_root).resolve()
    return Path(settings.BASE_DIR).resolve() / "staticfiles"
