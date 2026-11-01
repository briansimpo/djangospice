from django.contrib.admin.sites import NotRegistered
from django.contrib import admin
from django.conf import settings
from djangospice.package.routing import Routing


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


def admin_unregister(model):
    try:
        admin.site.unregister(model)
    except NotRegistered:
        pass

def get_domain_name():
    domain = getattr(settings, 'DJANGO_HOST')
    return f"{domain}"

def get_app_name(normalize=False):
    name = getattr(settings, "APP_NAME", None)
    if normalize:
        return str(name).capitalize()
    return name

def get_admin_app_title():
    app_name = get_app_name()
    return f"{app_name} Admin"

