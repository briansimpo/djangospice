from django.urls import path

from djangospice.package.routing import Routing
from djangospice.websocket.consumers import DefaultConsumer


def http_urlpatterns():
    urlpatterns = Routing.build_urlpatterns()
    return urlpatterns, None, None


def websocket_urlpatterns():
    return [
        path(
            "ws/realtime/",
            DefaultConsumer.as_asgi(),
            name="djangospice-realtime",
        ),
        *Routing.collect_urlpatterns(
            module_type="websocket",
            attribute="websocket_urlpatterns",
        ),
    ]

