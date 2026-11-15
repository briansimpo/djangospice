import re
import uuid
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


def get_template_name(template_path, app_name=None):
    # Check if the extension is missing and add it if necessary
    if not template_path.endswith('.html'):
        template_path += '.html'
        
    if app_name:
        return f"{app_name}/{template_path}"
    else:
        return template_path
        

def safe_reverse(view_name, app_name=None, args=None, kwargs=None, template=False):
    """
    Attempts multiple reverse patterns safely:
    1. app_name:view_name
    2. app_name_view_name
    3. view_name

    Supports args, kwargs, and URL templates.

    When template=True, placeholder identifies the URL keyword
    argument to replace with __ID__.

    Falls back to "/" if no match is found.
    """

    candidates = []

    if app_name:
        candidates.extend([
            f"{app_name}:{view_name}",
            f"{app_name}_{view_name}",
        ])

    candidates.append(view_name)

    if template:
        kwargs = {
            **(kwargs or {}),
            "pk": str(uuid.uuid4()),
        }

    for name in candidates:
        try:
            url = reverse(
                name,
                args=args or None,
                kwargs=kwargs or None,
            )

            if template:
                url = url.replace(kwargs["pk"], "__ID__")

            return url

        except NoReverseMatch:
            continue

    return "/"


def safe_action(app_name, action_name, args=None, kwargs=None):
    """
    Shortcut for reversing app_named actions.

    Uses lazy evaluation so URL resolution happens at render time, not
    app import/startup time.
    """
    lazy_safe_reverse = lazy(safe_reverse, str)
    return lazy_safe_reverse(
        view_name=action_name,
        app_name=app_name,
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
        app_name=app_name,
        args=args,
        kwargs=kwargs,
    )
    return redirect(url)

def redirect_to(view_name, args=None, kwargs=None):
    """
    Redirect without app_name.
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


    