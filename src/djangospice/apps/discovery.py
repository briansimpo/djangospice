from __future__ import annotations

import importlib
import inspect
import logging
import threading

from collections.abc import Callable
from types import ModuleType
from typing import TypeVar

from django.apps import apps

from .config import AppConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AppDiscovery:
    """
    A utility class responsible for discovering specific app types 
    within the installed Django application configurations.
    """

    def get_apps(self) -> list[AppConfig]:
        """
        Iterates through all installed Django app configs and filters 
        them to find instances of AppConfig.

        Returns:
            list[AppConfig]: A list of discovered AppConfig instances currently registered in the Django project.
        """
        return [
            config for config in apps.get_app_configs() 
            if isinstance(config, AppConfig)
        ]
        
        


class ModuleDiscovery:
    """
    Discovers modules from installed Django applications,
    inspects them for classes (optionally filtering by base class),
    and passes each discovered class to an optional callback.

    If no callback is provided, it acts as a standard autodiscovery
    mechanism, importing the modules to trigger side effects.
    """

    # Cache key format: (module_name, base_class, has_callback)
    _discovered: set[tuple[str, type | None, bool]] = set()
    _lock = threading.Lock()

    @classmethod
    def discover(
        cls,
        *,
        module: str,
        callback: Callable[[type], None] | None = None,
        base_class: type[T] | None = None,
    ) -> None:
        """
        Discover modules/classes from all installed applications.

        Args:
            module:
                Module name to discover (e.g. "widgets").

            callback:
                Optional callback invoked for every discovered class.

            base_class:
                Optional base class to search for.
        """
        has_callback = callback is not None
        key = (module, base_class, has_callback)

        if key in cls._discovered:
            return

        with cls._lock:

            if key in cls._discovered:
                return

            for app in apps.get_app_configs():

                module_name = f"{app.name}.{module}"

                try:
                    imported = importlib.import_module(module_name)

                except ModuleNotFoundError as ex:
                    # Ignore apps that don't expose the requested module.
                    if ex.name == module_name:
                        continue
                    raise

                except Exception:
                    logger.exception(
                        "Failed importing '%s'.",
                        module_name,
                    )
                    raise

                # Only run inspection if a callback was actually provided
                if callback is not None:
                    cls._inspect(
                        imported,
                        base_class,
                        callback,
                    )

            cls._discovered.add(key)

    @classmethod
    def _inspect(
        cls,
        module: ModuleType,
        base_class: type | None,
        callback: Callable[[type], None],
    ) -> None:
        """
        Inspect a module for classes.
        """
        for _, obj in inspect.getmembers(
            module,
            inspect.isclass,
        ):
            if base_class is not None:
                if obj is base_class:
                    continue
                if not issubclass(obj, base_class):
                    continue
            else:
                if obj.__module__ != module.__name__:
                    continue

            if inspect.isabstract(obj):
                continue

            callback(obj)

    @classmethod
    def reset(cls) -> None:
        """
        Reset discovery.
        """
        with cls._lock:
            cls._discovered.clear()