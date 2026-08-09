
DEFAULT_RENDERERS = {
    "html": {
        "BACKEND": "djangospice.response.renderers.HTMLRenderer",
    },
    "htmx": {
        "BACKEND": "djangospice.response.renderers.HTMXRenderer",
    },
    "json": {
        "BACKEND": "djangospice.response.renderers.JSONRenderer",
    },
    "text": {
        "BACKEND": "djangospice.response.renderers.TextRenderer",
    },
}

