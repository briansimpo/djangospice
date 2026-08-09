import json
from django import template
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()


@register.filter
def jsonify(obj):
    """
    Converts model or dict to JSON safely.
    """
    if hasattr(obj, "to_dict"):
        obj = obj.to_dict()

    return json.dumps(obj, cls=DjangoJSONEncoder)