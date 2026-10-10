import re
from django.urls import NoReverseMatch
from django.utils.safestring import mark_safe
from django import template
from djangospice.templates import get_template_name
from djangospice.routing import safe_reverse
from djangospice.htmx.apps import namespace

register = template.Library()

    

@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, "")


@register.filter
def get_attr_display(obj, attr_name):
    display_method = f"get_{attr_name}_display"
    if hasattr(obj, display_method):
        return getattr(obj, display_method)()
    return getattr(obj, attr_name, "")


@register.filter
def verbose_name(obj):
    return obj._meta.verbose_name.title()


@register.filter
def highlight_search(text, search_term):
    if not search_term or not text:
        return text
    
    text = str(text)
    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
    highlighted = pattern.sub(lambda m: f'<mark class="search-highlight">{m.group()}</mark>', text)
    return mark_safe(highlighted)


@register.filter
def object_url(object, url_name):
    try:
        return safe_reverse(url_name, args=[object.pk])
    except NoReverseMatch:
        return "#"


@register.inclusion_tag(filename=get_template_name("search/searchview.html", namespace),takes_context=True)
def htmx_search(context):
    return context


@register.inclusion_tag(filename=get_template_name("modal/modalview.html", namespace),takes_context=True)
def htmx_modal(context):
    return context


@register.inclusion_tag(filename=get_template_name("modal/confirm.html", namespace),takes_context=True)
def htmx_confirm(context):
    return context


@register.inclusion_tag(filename=get_template_name("tabs/tabview.html", namespace),takes_context=True)
def htmx_tabs(context):
    return context


