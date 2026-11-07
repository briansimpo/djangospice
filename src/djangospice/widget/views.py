from __future__ import annotations

from typing import Any

from django.views import View
from django.http import Http404, HttpRequest, HttpResponse

from djangospice.core.executable import ClassIdentity
from djangospice.htmx.shortcuts import render_response

from .resolver import WidgetResolver
from .exceptions import WidgetNotVisible
from .executor import WidgetExecutor


class WidgetView(View):
    """
    HTTP view for dynamically resolving, configuring, and executing widgets.

    Resolves a registered Widget using its app and class identity,
    then delegates execution to WidgetExecutor.
    """

    def dispatch(self, request: HttpRequest, app_name: str, class_name: str, action: str | None = None, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            identifier = ClassIdentity.build(app_name, class_name).to_string()

            widget_cls = WidgetResolver.resolve(identifier)

        except LookupError as exc:
            raise Http404(str(exc)) from exc

        widget_kwargs = {
            **request.GET.dict(),
            **kwargs,
        }

        widget = widget_cls(
            request=request,
            **widget_kwargs,
        )

        try:
            response = WidgetExecutor(widget, request, action=action).execute()

        except WidgetNotVisible:
            raise Http404(
                f"Widget '{app_name}:{class_name}' is not accessible."
            ) from None

        return render_response(request, response)