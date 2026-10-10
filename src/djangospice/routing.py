import re
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.urls import reverse, NoReverseMatch
from django.http import HttpRequest
from django.shortcuts import redirect
from django.utils.functional import lazy
from urllib.parse import urlparse


def get_view_name(view_name, app_name=None):
    if app_name is None:
        return view_name
    else:
        return f"{app_name}:{view_name}" 

def safe_reverse(view_name, namespace=None, args=None, kwargs=None):
    """
    Attempts multiple reverse patterns safely:
    1. namespace:view_name
    2. namespace_view_name
    3. view_name

    Supports both args and kwargs.
    Falls back to "/" if no match is found.
    """
    candidates = []

    if namespace:
        candidates.append(f"{namespace}:{view_name}")  # case 1
        candidates.append(f"{namespace}_{view_name}")  # case 2

    candidates.append(view_name)  # case 3

    for name in candidates:
        try:
            return reverse(name, args=args or None, kwargs=kwargs or None)
        except NoReverseMatch:
            continue

    return "/"

def safe_action(app_name, action_name, args=None, kwargs=None):
    """
    Shortcut for reversing namespaced actions.

    Uses lazy evaluation so URL resolution happens at render time, not
    app import/startup time.
    """
    lazy_safe_reverse = lazy(safe_reverse, str)
    return lazy_safe_reverse(
        view_name=action_name,
        namespace=app_name,
        args=args,
        kwargs=kwargs,
    )

def get_valid_url(url):
    validate = URLValidator()

    # Normalize multiple slashes while preserving the URL scheme.
    parsed_url = urlparse(url)

    if parsed_url.scheme and parsed_url.netloc:
        # Normalize only the path, query, and fragment.
        path = re.sub(r"/{2,}", "/", parsed_url.path)
        normalized_url = parsed_url._replace(path=path).geturl()

        try:
            validate(normalized_url)
            return normalized_url
        except ValidationError:
            return normalized_url

    # Normalize repeated slashes in relative and root-relative URLs.
    url = re.sub(r"/{2,}", "/", url)

    # Handle root-relative URLs.
    if url.startswith("/"):
        return url

    # Try resolving the URL as a Django view name.
    try:
        return reverse(url)
    except NoReverseMatch:
        pass

    # Validate and return the relative URL.
    try:
        validate(url)
        return url
    except ValidationError:
        return url

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