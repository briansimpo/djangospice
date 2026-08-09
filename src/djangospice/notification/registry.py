import importlib
import logging
import threading
from typing import Any

from django.core.exceptions import ImproperlyConfigured

from .channels import NotificationChannel
from .enums import Channel
from .conf import notification_settings

logger = logging.getLogger(__name__)


class ChannelRegistry:
    """
    Thread-safe registry for dynamically loading and caching notification 
    channel providers based on Django settings.
    """

    _providers: dict[Channel, NotificationChannel] = {}
    _initialized: bool = False
    _lock = threading.Lock()

    @classmethod
    def _load_channel(cls, config: dict[str, Any]) -> NotificationChannel:
        """
        Dynamically import and instantiate a notification channel class.

        Args:
            config (dict[str, Any]): The channel configuration dictionary.

        Returns:
            NotificationChannel: The instantiated provider.

        Raises:
            ImproperlyConfigured: If the backend path is missing or invalid.
        """
        options = config.copy()
        backend = options.pop("BACKEND", None)

        if not backend:
            raise ImproperlyConfigured("Provider configuration requires a 'BACKEND' key.")

        try:
            module_name, class_name = backend.rsplit(".", 1)
            app = importlib.import_module(module_name)
            channel_class = getattr(app, class_name)
            
            return channel_class(**options)

        except (ImportError, AttributeError, ValueError) as ex:
            raise ImproperlyConfigured(f"Cannot load notification backend '{backend}'.") from ex

    @classmethod
    def load(cls) -> None:
        """
        Load all providers defined in settings into the registry.
        Uses a double-checked locking pattern for thread safety during lazy initialization.
        """
        if cls._initialized:
            return

        with cls._lock:
            if cls._initialized:
                return

            for channel_key, config in notification_settings.PROVIDERS.items():
                # Cast the string key from settings to the strict Channel enum
                channel = Channel(channel_key)
                provider = cls._load_channel(config)

                # Validate that the settings key matches the provider's intrinsic channel class variable
                if provider.channel != channel:
                    raise ImproperlyConfigured(
                        f"Configured provider for '{channel.value}' reports its "
                        f"channel as '{provider.channel.value}'."
                    )

                cls._providers[channel] = provider

            cls._initialized = True

    @classmethod
    def get_provider(cls, channel: Channel | str) -> NotificationChannel | None:
        """
        Retrieve an instantiated provider for a given channel.

        Args:
            channel (Channel | str): The requested channel enum or its string value.

        Returns:
            NotificationChannel | None: The provider, or None if not registered/invalid.
        """
        if not cls._initialized:
            cls.load()

        # Safely normalize strings (e.g., from DB CharFields) into Enums for dict lookup
        try:
            channel_enum = Channel(channel)
        except ValueError:
            return None

        return cls._providers.get(channel_enum)

    @classmethod
    def providers(cls) -> dict[Channel, NotificationChannel]:
        """
        Return a shallow copy of all loaded providers.
        """
        if not cls._initialized:
            cls.load()

        return cls._providers.copy()

    @classmethod
    def channels(cls) -> tuple[Channel, ...]:
        """
        Return a tuple of all currently registered channel Enums.
        """
        if not cls._initialized:
            cls.load()

        return tuple(cls._providers.keys())