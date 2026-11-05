def is_djangospice_app(config) -> bool:
    """
    Identify Djangospice applications and extensions.
    """
    return getattr(config, "djangospice_app", False) is True
