from django.urls import include, path
from djangospice.apps import namespace

app_name = namespace

urlpatterns = [
    path(
        "notification/",
        include("djangospice.notification.urls"),
    ),
    path(
        "widget/",
        include("djangospice.widget.urls"),
    ),
    path(
        "lookup/",
        include("djangospice.lookup.urls"),
    ),
]