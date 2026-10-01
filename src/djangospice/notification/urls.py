from django.urls import path
from .apps import namespace
from . import views

app_name = namespace

urlpatterns = [
    # HTML
    path(
        "",
        views.AllNotificationsList.as_view(),
        name="all",
    ),
    path(
        "unread/",
        views.UnreadNotificationsList.as_view(),
        name="unread",
    ),

    # HTML actions
    path(
        "mark-all-as-read/",
        views.mark_all_as_read,
        name="mark-all-as-read",
    ),
    path(
        "<slug:slug>/read/",
        views.mark_as_read,
        name="mark-as-read",
    ),
    path(
        "<slug:slug>/unread/",
        views.mark_as_unread,
        name="mark-as-unread",
    ),
    path(
        "<slug:slug>/delete/",
        views.delete,
        name="delete",
    ),

    # JavaScript API
    path(
        "api/unread/",
        views.api_unread_notification_list,
        name="api-unread",
    ),
    path(
        "api/all/",
        views.api_all_notification_list,
        name="api-all",
    ),
    path(
        "api/unread/count/",
        views.api_unread_notification_count,
        name="api-unread-count",
    ),
    path(
        "api/all/count/",
        views.api_all_notification_count,
        name="api-all-count",
    ),
    path(
        "api/mark-all-as-read/",
        views.api_mark_all_as_read,
        name="api-mark-all-read",
    ),
    path(
        "api/<slug:slug>/read/",
        views.api_mark_as_read,
        name="api-mark-read",
    ),
    path(
        "api/<slug:slug>/unread/",
        views.api_mark_as_unread,
        name="api-mark-unread",
    ),
    path(
        "api/<slug:slug>/delete/",
        views.api_delete,
        name="api-delete",
    ),
]