from django.urls import include, path

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

