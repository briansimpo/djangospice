import threading

from django.core.exceptions import ImproperlyConfigured

from djangospice.exec.identity import ClassIdentity

from .mixin import Executable


class Registry:
    """Thread-safe registry for Executable classes."""

    instances: dict[str, type[Executable]] = {}
    _lock = threading.RLock()

    @classmethod
    def get_key(cls, exec_klass: type[Executable]) -> str:
        return ClassIdentity.from_class(exec_klass).to_string()

    @classmethod
    def register(cls, exec_klass: type[Executable]) -> type[Executable]:
        """Register a Executable class."""

        if not isinstance(exec_klass, type) or not issubclass(exec_klass, Executable):
            raise TypeError("Expected a Executable subclass.")

        if not exec_klass.class_name:
            raise ImproperlyConfigured(
                f"{exec_klass.__qualname__} must define a name."
            )

        if not exec_klass.app_name:
            raise ImproperlyConfigured(
                f"{exec_klass.__qualname__} must define an app_name."
            )

        key = cls.get_key(exec_klass)

        with cls._lock:
            existing = cls.instances.get(key)

            if existing is exec_klass:
                return exec_klass

            if existing is not None:
                raise ImproperlyConfigured(
                    f"Executable '{key}' is already registered by "
                    f"{existing.__module__}.{existing.__qualname__}."
                )

            cls.instances[key] = exec_klass

        return exec_klass

    @classmethod
    def unregister(cls, identifier: str) -> None:
        """Unregister a Executable by its identity."""

        with cls._lock:
            cls.instances.pop(identifier, None)

    @classmethod
    def unregister_app(cls, app_name: str) -> None:
        """Unregister all Widgets belonging to an application."""

        with cls._lock:
            keys = [
                key
                for key, exec_klass in cls.instances.items()
                if exec_klass.app_name == app_name
            ]

            for key in keys:
                del cls.instances[key]

    @classmethod
    def get(cls, identifier: str) -> type[Executable]:
        with cls._lock:
            try:
                return cls.instances[identifier]
            except KeyError:
                raise LookupError(
                    f"Executable '{identifier}' is not registered."
                ) from None

   
