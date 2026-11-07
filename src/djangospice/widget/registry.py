
import threading
from collections.abc import Iterator

from django.core.exceptions import ImproperlyConfigured

from djangospice.core.executable import ClassIdentity

from .widget import Widget


class WidgetRegistry:
    """Thread-safe registry for Widget classes."""

    widgets: dict[str, type[Widget]] = {}
    _lock = threading.RLock()

    @classmethod
    def get_key(cls, widget_klass: type[Widget]) -> str:
        return ClassIdentity.from_class(widget_klass).to_string()

    @classmethod
    def register(cls, widget_klass: type[Widget]) -> type[Widget]:
        """Register a Widget class."""

        if not isinstance(widget_klass, type) or not issubclass(widget_klass, Widget):
            raise TypeError("Expected a Widget subclass.")

        if not widget_klass.class_name:
            raise ImproperlyConfigured(
                f"{widget_klass.__qualname__} must define a name."
            )

        if not widget_klass.app_name:
            raise ImproperlyConfigured(
                f"{widget_klass.__qualname__} must define an app_name."
            )

        key = cls.get_key(widget_klass)

        with cls._lock:
            existing = cls.widgets.get(key)

            if existing is widget_klass:
                return widget_klass

            if existing is not None:
                raise ImproperlyConfigured(
                    f"Widget '{key}' is already registered by "
                    f"{existing.__module__}.{existing.__qualname__}."
                )

            cls.widgets[key] = widget_klass

        return widget_klass

    @classmethod
    def unregister(cls, identifier: str) -> None:
        """Unregister a Widget by its identity."""

        with cls._lock:
            cls.widgets.pop(identifier, None)

    @classmethod
    def unregister_app(cls, app_name: str) -> None:
        """Unregister all Widgets belonging to an application."""

        with cls._lock:
            keys = [
                key
                for key, widget_klass in cls.widgets.items()
                if widget_klass.app_name == app_name
            ]

            for key in keys:
                del cls.widgets[key]

    @classmethod
    def get(cls, identifier: str) -> type[Widget]:
        with cls._lock:
            try:
                return cls.widgets[identifier]
            except KeyError:
                raise LookupError(
                    f"Widget '{identifier}' is not registered."
                ) from None

   
