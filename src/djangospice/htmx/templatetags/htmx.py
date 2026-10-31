import re
from django.utils.safestring import mark_safe
from django import template
from djangospice.utils import get_template_name
from djangospice.htmx.apps import namespace

register = template.Library()

    
@register.filter
def highlight_search(text, search_term):
    if not search_term or not text:
        return text
    
    text = str(text)
    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
    highlighted = pattern.sub(lambda m: f'<mark class="search-highlight">{m.group()}</mark>', text)
    return mark_safe(highlighted)


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


