from django.http import HttpRequest
from django.shortcuts import redirect
from .urls import safe_reverse 


def safe_redirect(view_name, app_name=None, args=None, kwargs=None):
    """
    Safely reverse and redirect.
    """
    url = safe_reverse(
        view_name=view_name,
        namespace=app_name,
        args=args,
        kwargs=kwargs,
    )
    return redirect(url)

def redirect_to(view_name, args=None, kwargs=None):
    """
    Redirect without namespace.
    """
    url = safe_reverse(
        view_name=view_name,
        args=args,
        kwargs=kwargs,
    )
    return redirect(url)
    
def redirect_back(request: HttpRequest):
    referer = request.META.get("HTTP_REFERER")
    return redirect(referer)