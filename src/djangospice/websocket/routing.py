from django.urls import URLPattern, URLResolver
from djangospice.app_registry.module import Module


def websocket_urlpatterns() -> list[URLPattern | URLResolver]:
    """Collect WebSocket URL patterns from installed Django apps."""
    urlpatterns = []

    for module in Module.get_modules("websocket"):
        urlpatterns.extend(
            getattr(module, "websocket_urlpatterns", [])
        )

    return urlpatterns