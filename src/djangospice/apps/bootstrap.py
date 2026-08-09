from typing import Iterable
from djangospice.container import container
from .discovery import AppDiscovery
from .loader import AppLoader
from .config import AppConfig


class Bootstrap:
    """
    Coordinates the discovery, loading, registration, and initialization 
    of all djangospice framework apps.
    """

    def __init__(self) -> None:
        """Initializes components required to orchestrate application setup."""
        self.discovery = AppDiscovery()
        self.loader = AppLoader()

    def run(self) -> list[AppConfig]:
        """
        Executes the entire initialization pipeline for discovered apps.

        Returns:
            list[AppConfig]: An ordered list of successfully booted apps.
        """
        apps = self.discovery.get_apps()
        sorted_modules = self.loader.load(apps)
        
        self.register_apps(sorted_modules)
        container.start_singletons()
        self.boot_apps(sorted_modules)
        
        return sorted_modules

    def register_apps(self, apps: Iterable[AppConfig]) -> None:
        """
        Invokes individual registration hooks for each app.

        Args:
            apps (Iterable[AppConfig]): The collection of apps to register.
        """
        for app in apps:
            app.register()

    def boot_apps(self, apps: Iterable[AppConfig]) -> None:
        """
        Invokes individual lifecycle boot hooks for each app.

        Args:
            apps (Iterable[AppConfig]): The collection of apps to boot.
        """
        for app in apps:
            app.boot()