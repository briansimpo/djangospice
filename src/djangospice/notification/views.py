from __future__ import annotations

from typing import Any

from django.http import HttpRequest, HttpResponse
from django.views import View

class NotificationActionView(View):
 

    def dispatch(self, request: HttpRequest, app_name: str, class_name:str,  *args: Any, **kwargs: Any) -> HttpResponse:
        pass