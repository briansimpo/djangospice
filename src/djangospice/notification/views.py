from __future__ import annotations

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.encoding import iri_to_uri
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView

from djangospice.templates import get_template_name
from djangospice.urls import safe_reverse

from .apps import namespace
from .helpers import (
    dispatch_notification_deleted,
    dispatch_notification_read,
    dispatch_notification_unread,
    serialize_notification,
    serialize_notifications,
)
from .models import Notification
from .utils import slug2id


class NotificationViewList(ListView):
    template_name = get_template_name("list.html", namespace)
    context_object_name = "notifications"
    paginate_by = 25

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class AllNotificationsList(NotificationViewList):
    def get_queryset(self):
        return self.request.user.notifications.all()


class UnreadNotificationsList(NotificationViewList):
    def get_queryset(self):
        return self.request.user.notifications.unread()


def _redirect_next(request, fallback: str):
    next_url = request.GET.get("next")

    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        settings.ALLOWED_HOSTS,
    ):
        return redirect(iri_to_uri(next_url))

    return redirect(safe_reverse(fallback, namespace))


@login_required
@require_POST
def mark_all_as_read(request):
    with transaction.atomic():
        notifications = list(
            request.user.notifications.unread()
        )

        for notification in notifications:
            notification.mark_as_read()
            dispatch_notification_read(notification)

    return _redirect_next(request, "unread")


@login_required
@require_POST
def mark_as_read(request, slug=None):
    notification_id = slug2id(slug)

    notification = get_object_or_404(
        Notification,
        recipient=request.user,
        id=notification_id,
    )

    if notification.unread:
        notification.mark_as_read()
        dispatch_notification_read(notification)

    return _redirect_next(request, "unread")


@login_required
@require_POST
def mark_as_unread(request, slug=None):
    notification_id = slug2id(slug)

    notification = get_object_or_404(
        Notification,
        recipient=request.user,
        id=notification_id,
    )

    if not notification.unread:
        notification.mark_as_unread()
        dispatch_notification_unread(notification)

    return _redirect_next(request, "unread")


@login_required
@require_POST
def delete(request, slug=None):
    notification_id = slug2id(slug)

    notification = get_object_or_404(
        Notification,
        recipient=request.user,
        id=notification_id,
    )

    dispatch_notification_deleted(notification)
    notification.delete()

    return _redirect_next(request, "all")


@login_required
@require_GET
@never_cache
def api_unread_notification_list(request):
    notifications = request.user.notifications.unread()

    return JsonResponse(
        {
            "unread_count": notifications.count(),
            "unread_list": serialize_notifications(notifications),
        }
    )


@login_required
@require_GET
@never_cache
def api_all_notification_list(request):
    notifications = request.user.notifications.all()

    return JsonResponse(
        {
            "all_count": notifications.count(),
            "all_list": serialize_notifications(notifications),
        }
    )


@login_required
@require_GET
@never_cache
def api_unread_notification_count(request):
    return JsonResponse(
        {
            "unread_count": (
                request.user.notifications.unread().count()
            ),
        }
    )


@login_required
@require_GET
@never_cache
def api_all_notification_count(request):
    return JsonResponse(
        {
            "all_count": request.user.notifications.count(),
        }
    )


@login_required
@require_POST
@never_cache
def api_mark_as_read(request, slug=None):
    notification_id = slug2id(slug)

    notification = get_object_or_404(
        Notification,
        recipient=request.user,
        id=notification_id,
    )

    if notification.unread:
        notification.mark_as_read()
        dispatch_notification_read(notification)

    return JsonResponse(
        {
            "notification": serialize_notification(notification),
        }
    )


@login_required
@require_POST
@never_cache
def api_mark_as_unread(request, slug=None):
    notification_id = slug2id(slug)

    notification = get_object_or_404(
        Notification,
        recipient=request.user,
        id=notification_id,
    )

    if not notification.unread:
        notification.mark_as_unread()
        dispatch_notification_unread(notification)

    return JsonResponse(
        {
            "notification": serialize_notification(notification),
        }
    )


@login_required
@require_POST
@never_cache
def api_mark_all_as_read(request):
    with transaction.atomic():
        notifications = list(
            request.user.notifications.unread()
        )

        for notification in notifications:
            notification.mark_as_read()
            dispatch_notification_read(notification)

    return JsonResponse(
        {
            "unread_count": 0,
        }
    )


@login_required
@require_POST
@never_cache
def api_delete(request, slug=None):
    notification_id = slug2id(slug)

    notification = get_object_or_404(
        Notification,
        recipient=request.user,
        id=notification_id,
    )

    dispatch_notification_deleted(notification)
    notification.delete()

    return JsonResponse(
        {
            "id": str(notification_id),
            "deleted": True,
        }
    )