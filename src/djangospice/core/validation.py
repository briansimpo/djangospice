from django.core.validators import validate_email
from django.core.exceptions import ValidationError


def is_valid_email(email: str) -> bool:
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False

def has_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True
