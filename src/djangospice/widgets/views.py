from django.views import View
from django.http import HttpRequest, Http404
from djangospice.response.shortcuts import render_response

from .runtime import WidgetExecutor
from .registry import WidgetRegistry


class WidgetView(View):

    def dispatch(self, request: HttpRequest, app_label:str, name: str, *args, **kwargs):
        widget_key = f"{app_label}.{name}"
        
        widget_cls = WidgetRegistry.get(widget_key)

        if widget_cls is None:
            raise Http404()

        widget = widget_cls(
            request=request,
            **request.GET.dict(),
        )

        response = WidgetExecutor(widget, request).execute()

        return render_response(response, request)