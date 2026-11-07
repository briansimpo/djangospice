from django.urls import path

from .views import NotificationActionView
from .apps import namespace

app_name = namespace

urlpatterns = [
    path(
        f"<slug:app_name>/<slug:class_name>/",
        NotificationActionView.as_view(),
        name="notification_action",
    ),
]