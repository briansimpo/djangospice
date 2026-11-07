from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.views import View
from django.http import Http404, HttpRequest, HttpResponse

from djangospice.exec.identity import ClassIdentity
from djangospice.exec.resolver import Resolver
from djangospice.htmx.shortcuts import dispatch_response

from .executor import NotificationExecutor


class NotificationView(View):
   

    def dispatch(self, request: HttpRequest, app_name: str, class_name: str, action: str | None = None, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            notification_id = (
                request.POST.get("notification_id")
                or request.GET.get("notification_id")
            )

            notification_model = get_object_or_404(
                request.user.notifications,
                pk=notification_id,
            )
        except Exception:
            raise Http404()

        try:
            identifier = ClassIdentity.build(app_name, class_name).to_string()

            executable = Resolver.resolve(identifier)

        except LookupError as exc:
            raise Http404(str(exc)) from exc

        exec_kwargs = {
            **request.GET.dict(),
            **kwargs,
        }

        instance = executable(
            request=request,
            notification_model=notification_model,
            **exec_kwargs,
        )

        try:
            response = NotificationExecutor(notification=instance, request=request, action=action).execute()

        except PermissionDenied:
            raise Http404() from None

        return dispatch_response(request, response)