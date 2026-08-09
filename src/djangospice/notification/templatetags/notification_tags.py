from django import template
from djangospice.notification.alert import Alert

register = template.Library()

template_name = Alert.get_template_name()


@register.inclusion_tag(template_name, takes_context=True)
def render_alerts(context):
    """
    Renders the toast partial on initial page load.
    The 'messages' framework is automatically injected into the context 
    by django.contrib.messages.context_processors.messages.
    """
    return {
        'messages': context.get('messages', []),
        'oob': False # False on page load, so it renders inline normally
    }