
def safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def safe_bool(value):
    if isinstance(value, str):
        value = value.strip().lower()
        if value in ['true', '1', 'yes']:
            return True
        elif value in ['false', '0', 'no']:
            return False
    elif isinstance(value, (int, bool)):
        return bool(value)
    return None