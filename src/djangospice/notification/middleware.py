from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.contrib.messages import get_messages
from djangospice.response.response import Response
from djangospice.notification.alert import Alert


class NotificationMiddleware:
    """
    Converts standard Django flash messages into Out-Of-Band HTMX partials.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        
        if (request.headers.get("HX-Request") != "true" or not isinstance(response, Response)):
            return response

        messages = list(get_messages(request))

        if messages:
            fragment = Alert.fragment(messages)
            response.add_fragment(fragment)
            
        return response