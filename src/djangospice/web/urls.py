from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.urls import include, reverse, NoReverseMatch
from django.utils.functional import lazy
from urllib.parse import urljoin, urlparse, urlsplit
from django.conf import settings

def get_host_name(host_name=None, port=None):
    # Determine the scheme based on whether SSL redirection is enabled
    is_secure = getattr(settings, 'SECURE_SSL_REDIRECT', False)
    scheme = 'https' if is_secure else 'http'

    # Use the provided host name or fall back to the setting
    host_name = host_name or getattr(settings, 'DJANGO_HOST', 'localhost')
    port = port or getattr(settings, 'DJANGO_PORT', None)

    # Include the port if specified and not using HTTPS
    port_part = f":{port}" if port and not is_secure else ''

    # Construct the full host name
    return f"{scheme}://{host_name}{port_part}"

def get_socket_host(request=None, host_name=None, port=None):
    if request:
        scheme = "wss" if request.is_secure() else "ws"

        # urlsplit needs a scheme to parse correctly
        split = urlsplit(f"//{request.get_host()}")
        host = split.hostname

        socket_port = getattr(settings, "DJANGO_SOCKET_PORT", None)

        if socket_port:
            return f"{scheme}://{host}:{socket_port}"

        return f"{scheme}://{host}"

    is_secure = getattr(settings, "SECURE_SSL_REDIRECT", False)
    scheme = "wss" if is_secure else "ws"

    host_name = host_name or getattr(settings, "DJANGO_SOCKET_HOST", "localhost")
    port = port or getattr(settings, "DJANGO_SOCKET_PORT", None)

    port_part = f":{port}" if port else ""
    return f"{scheme}://{host_name}{port_part}"

def get_absolute_uri(view_name:str, host_name:str=None):
    relative_url = reverse(view_name)
    host = get_host_name(host_name)
    absolute_url = build_absolute_uri(host, relative_url)
    return absolute_url

def build_absolute_uri(host:str, relative_url:str):
    uri = urljoin(f"{host.rstrip('/')}/", relative_url.lstrip('/'))
    return uri

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

def action(app_name, action_name, args=None, kwargs=None):
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
    
    # Parse the URL to determine if it's absolute or relative
    parsed_url = urlparse(url)

    # If the URL has a scheme and netloc, it's an absolute URL
    if parsed_url.scheme and parsed_url.netloc:
        try:
            validate(url)  # Validate the absolute URL
            return url  # Return the absolute URL as it is
        except ValidationError:
            return url  # If the absolute URL is invalid, return it as is
        
    # Handle root-relative URLs (with or without trailing slashes)
    if url.startswith('/'):
        return url  # Return the root-relative URL as is
    
    # Try to resolve the URL as a Django view name
    try:
        # If it's a valid view name, reverse it to get the URL
        return reverse(url)
    except NoReverseMatch:
        pass  # If no matching view name, continue to validate as relative URL
    
    # Finally, validate and return the relative URL
    try:
        validate(url)  # Check if it's a valid relative URL
        return url
    except ValidationError:
        return url  # If not valid, return as is or handle accordingly

def include_urls(namespace, subfolder=None):
    if subfolder:
        return include(f"{namespace}.{subfolder}.urls")
    else:
        return include(f"{namespace}.urls")