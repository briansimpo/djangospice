from .utils import get_admin_app_title, get_app_name
from .spice.routing import websocket_urlpatterns, http_urlpatterns
from .package.shotcuts import packages


__all__ = [
    "get_admin_app_title",
    "get_app_name",
    "websocket_urlpatterns",
    "http_urlpatterns",
    "packages"
]