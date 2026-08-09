from __future__ import annotations

import importlib
import logging
import threading
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest

from .conf import response_settings
from .renderers import BaseRenderer

logger = logging.getLogger(__name__)


class RendererRegistry:
    """
    Thread-safe registry for response renderers.

    Renderers may be registered in two ways:
    1. Declaratively through RESPONSE_RENDERERS settings.
    2. Programmatically using ``register()`` (typically from AppConfig.ready()).
    """

    _renderers: dict[str, BaseRenderer] = {}
    _initialized = False
    _lock = threading.RLock()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    @classmethod
    def _load_renderer(cls, config: dict[str, Any]) -> BaseRenderer:
        """
        Dynamically import and instantiate a renderer from configuration.

        Args:
            config: A dictionary containing configuration options for the
                renderer. Must include a 'BACKEND' key pointing to the class path.

        Returns:
            An instantiated instance of ResponseRenderer.

        Raises:
            ImproperlyConfigured: If 'BACKEND' is missing, the class cannot
                be loaded, or the loaded class is not a subclass of ResponseRenderer.
        """
        options = config.copy()
        backend = options.pop("BACKEND", None)

        if not backend:
            raise ImproperlyConfigured(
                "Renderer configuration requires a 'BACKEND' key."
            )

        try:
            module_name, class_name = backend.rsplit(".", 1)
            module = importlib.import_module(module_name)
            renderer_class = getattr(module, class_name)
            renderer = renderer_class(**options)
        except (ImportError, AttributeError, ValueError) as ex:
            raise ImproperlyConfigured(
                f"Cannot load response renderer '{backend}'."
            ) from ex

        if not isinstance(renderer, BaseRenderer):
            raise ImproperlyConfigured(
                f"'{backend}' is not a ResponseRenderer."
            )

        return renderer

    @classmethod
    def load(cls) -> None:
        """
        Load renderers from Django settings.

        This method is safe to call multiple times; subsequent calls will
        be treated as a no-op if the registry is already initialized.

        Raises:
            ImproperlyConfigured: If a loaded renderer's internal name does
                not match its configuration key in settings.
        """
        if cls._initialized:
            return

        with cls._lock:
            if cls._initialized:
                return

            for name, config in response_settings.RENDERERS.items():
                renderer = cls._load_renderer(config)

                if renderer.name != name:
                    raise ImproperlyConfigured(
                        f"Configured renderer '{name}' "
                        f"reports its name as '{renderer.name}'."
                    )

                cls.register(renderer)

            cls._initialized = True

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    @classmethod
    def register(cls,renderer: BaseRenderer,*, replace: bool = False) -> BaseRenderer:
        """
        Register a renderer instance programmatically.

        Typically used by AppConfig.ready() for explicit renderer registrations.

        Args:
            renderer: An instance of ResponseRenderer to register.
            replace: If True, allows overwriting an already registered renderer
                sharing the same name. Defaults to False.

        Returns:
            The registered ResponseRenderer instance.

        Raises:
            ImproperlyConfigured: If the provided renderer is not an instance of
                ResponseRenderer, or if a renderer with the same name is already
                registered and `replace` is False.
        """
        if not isinstance(renderer, BaseRenderer):
            raise ImproperlyConfigured(
                f"{renderer!r} is not a ResponseRenderer."
            )

        with cls._lock:
            existing = cls._renderers.get(renderer.name)

            if existing and not replace:
                raise ImproperlyConfigured(
                    f"Renderer '{renderer.name}' is already registered."
                )

            cls._renderers[renderer.name] = renderer

            logger.debug(
                "Registered renderer '%s' (%s)",
                renderer.name,
                renderer.__class__.__name__,
            )

        return renderer

    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Remove a renderer from the registry by its name.

        Args:
            name: The string name of the renderer to unregister.
        """
        with cls._lock:
            cls._renderers.pop(name, None)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    @classmethod
    def get_renderer(cls, name: str) -> BaseRenderer | None:
        """
        Retrieve a registered renderer by name.

        Args:
            name: The string name of the renderer.

        Returns:
            The ResponseRenderer instance if found, otherwise None.
        """
        if not cls._initialized:
            cls.load()

        return cls._renderers.get(name)

    @classmethod
    def has_renderer(cls, name: str) -> bool:
        """
        Check if a renderer is registered under the given name.

        Args:
            name: The string name to check.

        Returns:
            True if the renderer exists in the registry, False otherwise.
        """
        if not cls._initialized:
            cls.load()

        return name in cls._renderers

    @classmethod
    def renderers(cls) -> tuple[BaseRenderer, ...]:
        """
        Get all registered renderers sorted by their priority attribute.

        Returns:
            A tuple of sorted ResponseRenderer instances.
        """
        if not cls._initialized:
            cls.load()

        return tuple(
            sorted(
                cls._renderers.values(),
                key=lambda renderer: renderer.priority,
            )
        )

    @classmethod
    def renderer_names(cls) -> tuple[str, ...]:
        """
        Get the names of all currently registered renderers.

        Returns:
            A tuple of string names representing the registered renderers.
        """
        if not cls._initialized:
            cls.load()

        return tuple(cls._renderers.keys())

    @classmethod
    def resolve(cls, request: HttpRequest) -> BaseRenderer:
        """
        Resolve the most appropriate renderer to handle the incoming request.

        Evaluates renderers sequentially based on their priority ranking.

        Args:
            request: The incoming Django HttpRequest instance.

        Returns:
            The first ResponseRenderer instance that supports the request.

        Raises:
            ImproperlyConfigured: If no registered renderer supports the request.
        """
        if not cls._initialized:
            cls.load()

        for renderer in cls.renderers():
            if renderer.supports(request):
                return renderer

        raise ImproperlyConfigured(
            "No response renderer supports this request."
        )
        
    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @classmethod
    def clear(cls) -> None:
        """
        Clear all renderers from the registry and reset initialization state.
        """
        with cls._lock:
            cls._renderers.clear()
            cls._initialized = False

    @classmethod
    def reload(cls) -> None:
        """
        Wipe the current registry cache and reload all renderers from settings.
        """
        cls.clear()
        cls.load()