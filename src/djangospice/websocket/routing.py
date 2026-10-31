from django.urls import URLPattern, URLResolver, path

from djangospice.package.module import Module
from .consumers import DefaultConsumer


def websocket_urlpatterns() -> list[URLPattern | URLResolver]:
    """
    Collect Djangospice and extension WebSocket URL patterns.

    The framework provides a default websocket endpoint. Installed
    modules can contribute additional WebSocket endpoints through
    their `websocket_urlpatterns`.
    """
    urlpatterns = [
        path("ws/realtime/",  DefaultConsumer.as_asgi(), name="djangospice-realtime"),
    ]

    for module in Module.get_modules("websocket"):
        urlpatterns.extend(
            getattr(module, "websocket_urlpatterns", [])
        )

    return urlpatterns