from typing import Iterable
from .config import AppConfig
from .registry import registry


class AppLoader:
    """
    A loader responsible for topologically sorting and registering application apps.
    
    Attributes:
        loaded (list[AppConfig]): Apps loaded and registered in this instance.
    """

    def __init__(self) -> None:
        """Initializes the AppLoader with an empty list of loaded apps."""
        self.loaded: list[AppConfig] = []

    def load(self, apps: Iterable[AppConfig]) -> list[AppConfig]:
        """
        Sorts the provided apps by their dependencies and registers them.

        Args:
            apps (Iterable[AppConfig]): An iterable of app objects to load.

        Returns:
            list[AppConfig]: A cumulative list of apps loaded by this instance.
        """
        sorted_modules = self.sort(apps)

        for app in sorted_modules:
            registry.register(app)
            self.loaded.append(app)

        return self.loaded

    def sort(self, apps: Iterable[AppConfig]) -> list[AppConfig]:
        """
        Performs a topological sort on the apps using Depth First Search (DFS).

        Args:
            apps (Iterable[AppConfig]): The apps to sort.

        Raises:
            RuntimeError: If a circular dependency is detected.
            RuntimeError: If a declared dependency is missing from the provided apps.

        Returns:
            list[AppConfig]: A list of apps sorted such that dependencies appear 
                                before the apps that depend on them.
        """
        resolved: list[AppConfig] = []
        visited: set[str] = set()
        path: set[str] = set()

        # Map app names to their actual objects for quick retrieval
        module_map: dict[str, AppConfig] = {
            app.name: app for app in apps
        }

        def resolve(app: AppConfig) -> None:
            """Recursively resolves dependencies for a given app via DFS."""
            if app.name in visited:
                return

            if app.name in path:
                raise RuntimeError(f"Circular dependency detected in app '{app.name}'")

            path.add(app.name)

            dependencies = getattr(app, "dependencies", [])
            for dependency_name in dependencies:
                if dependency_name not in module_map:
                    raise RuntimeError(
                        f"Missing dependency: '{dependency_name}' required by '{app.name}'"
                    )
                resolve(module_map[dependency_name])

            path.remove(app.name)
            visited.add(app.name)
            resolved.append(app)

        for app in apps:
            resolve(app)

        return resolved