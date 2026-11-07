from django.urls import path

from .views import NotificationView
from .apps import namespace

app_name = namespace

urlpatterns = [
    path(
        "<slug:app_name>/<slug:class_name>/",
        NotificationView.as_view(),
        name="notification_view",
    ),
    path(
        "<slug:app_name>/<slug:class_name>/<slug:action>/",
        NotificationView.as_view(),
        name="notification_action",
    ),
]