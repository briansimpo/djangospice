from __future__ import annotations

from typing import Any, ClassVar

from django.core.exceptions import PermissionDenied
from django.views import View
from django.http import Http404, HttpRequest, HttpResponse
from djangospice.exec.dispatchers import Dispatcher, MethodDispatcher, UnknownDispatcher
from djangospice.exec.identity import ClassIdentity
from djangospice.exec.resolver import Resolver
from djangospice.htmx.shortcuts import dispatch

from .dispatchers import ActionDispatcher, HttpDispatcher


class WidgetView(View):

    
    dispatchers: ClassVar[tuple[type[Dispatcher], ...]] = (
        ActionDispatcher,
        MethodDispatcher,
        UnknownDispatcher,
        HttpDispatcher,
    )
   

    def dispatch(self, request: HttpRequest, app_name: str, class_name: str, action: str | None = None, *args: Any, **kwargs: Any) -> HttpResponse:

        try:
            identifier = ClassIdentity.build(app_name, class_name).to_string()
            executable = Resolver.resolve(identifier)

        except LookupError as exc:
            raise Http404(str(exc)) from exc

        try:
            params = {
                **request.GET.dict(),
                **kwargs,
            }

            instance = executable(**params)

            instance.set_request(request)

            instance.initialize()
            instance.configure()
            instance.authorize()

            for dispatcher_cls in self.dispatchers:
                dispatcher = dispatcher_cls(instance, request, action=action)
                if dispatcher.can_dispatch():
                    response = dispatcher.dispatch()
                    return dispatch(request, response)
                
            raise LookupError("No valid dispatcher found for this instance.")

        except PermissionDenied:
            raise Http404() from None
