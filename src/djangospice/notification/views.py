from __future__ import annotations

from typing import Any

from django.views import View
from django.http import Http404, HttpRequest, HttpResponse

from djangospice.exec.identity import ClassIdentity
from djangospice.exec.resolver import Resolver
from djangospice.htmx.shortcuts import dispatch_response

from .executor import NotificationExecutor


class NotificationView(View):
   

    def dispatch(self, request: HttpRequest, app_name: str, class_name: str, action: str | None = None, *args: Any, **kwargs: Any) -> HttpResponse:
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
            **exec_kwargs,
        )

        try:
            response = NotificationExecutor(notification=instance, request=request, action=action).execute()

        except Exception:
            raise Http404(
                f"Notification '{app_name}:{class_name}' is not accessible."
            ) from None

        return dispatch_response(request, response)