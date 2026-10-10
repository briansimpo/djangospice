from __future__ import annotations

from djangospice.routing import safe_reverse
from django.http import HttpRequest, HttpResponse

from .renderer import ResponseRenderer
from .response import Response

renderer = ResponseRenderer()


def render_response(request: HttpRequest, response: Response | HttpResponse) -> HttpResponse:
    if isinstance(response, Response):
        return renderer.render(response, request)

    return response



def htmx_render(request, template, context=None, **kwargs):
    """
    Renders a partial with stateless Message objects.
    'alerts' can be a string, a Message object, or a list of either.
    """

    response = Response.render(template=template, context=context, values=kwargs)
    return render_response(request=request, response=response)



def htmx_redirect(url, **kwargs):
    """
    Shortcut for HTMX-native redirects (HX-Location).
    Usage: return htmx_redirect('/dashboard/')
    """
    response = Response.redirect_to(url,kwargs=kwargs)
    return response


def htmx_safe_redirect(view_name, app_name=None, args=None, **kwargs):
    url = safe_reverse(view_name, app_name, args)
    return htmx_redirect(url, **kwargs)

