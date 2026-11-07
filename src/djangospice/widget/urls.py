from django.urls import path

from .views import WidgetView
from .apps import namespace

app_name = namespace

urlpatterns = [
    path(
        "<slug:app_name>/<slug:class_name>/",
        WidgetView.as_view(),
        name="widget_view",
    ),
    path(
        "<slug:app_name>/<slug:class_name>/<slug:action>/",
        WidgetView.as_view(),
        name="widget_action",
    ),
]