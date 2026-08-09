from django.contrib.admin.sites import NotRegistered
from django.contrib import admin
from django.conf import settings
from django.templatetags.static import static

def safe_unregister(model):
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


def get_default_site_logo():
    logo = getattr(settings, "SITE_LOGO")
    return static(logo)


def get_default_site_icon():
    logo = getattr(settings, "SITE_ICON")
    return static(logo)
