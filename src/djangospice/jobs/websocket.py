
from django.urls import path

from .consumers import JobConsumer

websocket_urlpatterns = [
    path(
        "ws/jobs/",
        JobConsumer.as_asgi(),
        name="ws-jobs",
    ),
]