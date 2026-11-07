from django.urls import path

from .views import NotificationActionView
from .apps import namespace

app_name = namespace

urlpatterns = [
    path(
        "<slug:app_name>/<slug:class_name>/",
        NotificationActionView.as_view(),
        name="notification_view",
    ),
    path(
        "<slug:app_name>/<slug:class_name>/<slug:action>/",
        NotificationActionView.as_view(),
        name="notification_action",
    ),
]