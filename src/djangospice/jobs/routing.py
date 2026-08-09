from django.urls import path
from .consumers import JobConsumer

websocket_urlpatterns = [
    path("ws/jobs/<str:job_id>/", JobConsumer.as_asgi()),
]