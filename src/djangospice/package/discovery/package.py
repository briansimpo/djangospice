
from __future__ import annotations

import inspect
from dataclasses import dataclass
from importlib import import_module
from importlib.metadata import entry_points
from pathlib import Path
from typing import Iterable, Literal

from django.apps import AppConfig as DjangoAppConfig
from django.core.exceptions import ImproperlyConfigured
from djangospice.package.config import AppConfig as DjangospiceAppConfig


@dataclass
class DiscoveredPackage:
    """A discovered Django application."""

    entry: str
    config: DjangoAppConfig
    source: Literal["builtin", "project", "extension", "explicit"]

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def label(self) -> str:
        return self.config.label

    @property
    def is_djangospice(self) -> bool:
        return isinstance(self.config, DjangospiceAppConfig)

    @property
    def enabled(self) -> bool:
        return getattr(self.config, "app_enabled", True)


class PackageDiscovery:
    """
    Discover, validate, resolve and register Django applications.

    Sources:
        - Built-in Djangospice applications.
        - Project-root applications.
        - Configured project application directories.
        - Installed Djangospice extensions.
        - Explicit INSTALLED_APPS entries.

    All discovery happens before django.setup().
    """

    ENTRY_POINT_GROUP = "djangospice.apps"

    def __init__(
        self,
        project_dir: str | Path,
        installed_apps: Iterable[str] = (),
        app_directories: Iterable[str] = ("apps",),
        package_name: str = "djangospice",
    ):
        self.project_dir = Path(project_dir).resolve()
        self.installed_apps = list(installed_apps)
        self.app_directories = tuple(app_directories)

        self.package_name = package_name
        self.package_dir = Path(
            import_module(package_name).__file__
        ).resolve().parent

        self._discovered: list[DiscoveredPackage] = []

    # ---------------------------------------------------------
    # General helpers
    # ---------------------------------------------------------

    def _is_private(self, path: Path) -> bool:
        return any(part.startswith("_") for part in path.parts)

    @staticmethod
    def _is_valid_package(directory: Path, root: Path) -> bool:
        try:
            relative = directory.relative_to(root)
        except ValueError:
            return False

        current = root

        for part in relative.parts:
            current /= part

            if not (current / "__init__.py").is_file():
                return False

        return True

    def _resolve(self, entry: str) -> DjangoAppConfig:
        try:
            return DjangoAppConfig.create(entry)
        except Exception as exc:
            raise ImproperlyConfigured(
                f"Could not load Django application '{entry}': {exc}"
            ) from exc

    @staticmethod
    def _config_path(config_class: type) -> str:
        return (
            f"{config_class.__module__}."
            f"{config_class.__qualname__}"
        )

    def _is_internal(self, config: DjangoAppConfig) -> bool:
        return (
            config.name == self.package_name
            or config.name.startswith(f"{self.package_name}.")
        )

    def _is_djangospice_config(self, config: DjangoAppConfig) -> bool:
        return isinstance(config, DjangospiceAppConfig)

    # ---------------------------------------------------------
    # Config discovery
    # ---------------------------------------------------------

    def _discover_config_classes(self, module_path: str) -> list[str]:
        module = import_module(module_path)
        discovered = []

        for _, cls in inspect.getmembers(
            module,
            inspect.isclass,
        ):
            if cls.__module__ != module.__name__:
                continue

            if cls is DjangospiceAppConfig:
                continue

            if not issubclass(cls, DjangospiceAppConfig):
                continue

            if inspect.isabstract(cls):
                continue

            if not getattr(cls, "name", None):
                raise ImproperlyConfigured(
                    f"{self._config_path(cls)} must define name."
                )

            discovered.append(self._config_path(cls))

        return discovered

    # ---------------------------------------------------------
    # Built-in Djangospice applications
    # ---------------------------------------------------------

    def discover_builtin(self) -> list[DiscoveredPackage]:
        discovered = []

        for apps_file in sorted(
            self.package_dir.rglob("apps.py")
        ):
            directory = apps_file.parent

            relative = directory.relative_to(
                self.package_dir
            )

            if not relative.parts:
                continue

            if self._is_private(relative):
                continue

            if not self._is_valid_package(
                directory,
                self.package_dir,
            ):
                continue

            # Give Django the application package, not apps.py.
            entry = ".".join((
                self.package_name,
                *relative.parts,
            ))

            discovered.append(
                DiscoveredPackage(
                    entry=entry,
                    config=self._resolve(entry),
                    source="builtin",
                )
            )

        return discovered

    # ---------------------------------------------------------
    # Project applications
    # ---------------------------------------------------------

    def discover_project(self) -> list[DiscoveredPackage]:
        discovered = []
        visited = set()

        def process(apps_file: Path):
            directory = apps_file.parent

            if directory in visited:
                return

            visited.add(directory)

            try:
                relative = directory.relative_to(
                    self.project_dir
                )
            except ValueError:
                return

            if not relative.parts:
                return

            if self._is_private(relative):
                return

            if relative.parts[0] == self.package_name:
                return

            if not self._is_valid_package(
                directory,
                self.project_dir,
            ):
                return

            module_path = ".".join(
                (*relative.parts, "apps")
            )

            for entry in self._discover_config_classes(
                module_path
            ):
                discovered.append(
                    DiscoveredPackage(
                        entry=entry,
                        config=self._resolve(entry),
                        source="project",
                    )
                )

        # Project-root apps: users, accounts, auth, etc.
        for directory in sorted(
            self.project_dir.iterdir()
        ):
            if not directory.is_dir():
                continue

            apps_file = directory / "apps.py"

            if apps_file.is_file():
                process(apps_file)

        # Nested apps: apps/organization, apps/members, etc.
        for app_directory in self.app_directories:
            root = (
                self.project_dir / app_directory
            ).resolve()

            if not root.is_dir():
                continue

            if not self._is_valid_package(
                root,
                self.project_dir,
            ):
                continue

            for apps_file in sorted(
                root.rglob("apps.py")
            ):
                process(apps_file)

        return discovered

    # ---------------------------------------------------------
    # Third-party extensions
    # ---------------------------------------------------------

    def discover_extensions(self) -> list[DiscoveredPackage]:
        discovered = []

        for entry_point in sorted(
            entry_points(group=self.ENTRY_POINT_GROUP),
            key=lambda item: item.name,
        ):
            config_class = entry_point.load()

            if not inspect.isclass(config_class):
                raise ImproperlyConfigured(
                    f"Invalid extension: {entry_point.name}"
                )

            if not issubclass(
                config_class,
                DjangospiceAppConfig,
            ):
                raise ImproperlyConfigured(
                    f"{entry_point.value} must inherit "
                    "from Djangospice AppConfig."
                )

            if inspect.isabstract(config_class):
                continue

            entry = self._config_path(config_class)

            discovered.append(
                DiscoveredPackage(
                    entry=entry,
                    config=self._resolve(entry),
                    source="extension",
                )
            )

        return discovered

    # ---------------------------------------------------------
    # Explicit applications
    # ---------------------------------------------------------

    def discover_explicit(self) -> list[DiscoveredPackage]:
        discovered = []

        for entry in self.installed_apps:
            config = self._resolve(entry)

            # Built-in apps are handled by internal discovery.
            if self._is_internal(config):
                continue

            discovered.append(
                DiscoveredPackage(
                    entry=entry,
                    config=config,
                    source="explicit",
                )
            )

        return discovered


    
    # ---------------------------------------------------------
    # Deduplication
    # ---------------------------------------------------------

    def deduplicate(self, applications: list[DiscoveredPackage]) -> list[DiscoveredPackage]:
        """
        Deduplicate by Django application name.

        Different applications cannot share the same Django label.
        """
        result = []
        names = {}
        labels = {}

        for application in applications:
            config = application.config

            if config.name in names:
                continue

            existing = labels.get(config.label)

            if existing and existing != config.name:
                raise ImproperlyConfigured(
                    f"Duplicate Django application label "
                    f"'{config.label}': '{existing}' and "
                    f"'{config.name}'."
                )

            names[config.name] = application
            labels[config.label] = config.name

            result.append(application)

        return result

    # ---------------------------------------------------------
    # Application dependencies
    # ---------------------------------------------------------

    @staticmethod
    def _dependency_identifier(dependency) -> str:
        """
        Resolve a dependency into an application identifier.

        Supported values:
            - Application key strings.
            - Objects exposing app_key, key, name or package.
        """
        if isinstance(dependency, str):
            return dependency

        for attribute in (
            "app_key",
            "key",
            "name",
            "package",
        ):
            value = getattr(dependency, attribute, None)

            if isinstance(value, str) and value.strip():
                return value.strip()

        raise ImproperlyConfigured(
            f"Invalid application dependency: {dependency!r}. "
            "A dependency must be a string or expose "
            "app_key, key, name or package."
        )

    def resolve_dependencies(self, applications: list[DiscoveredPackage]) -> list[DiscoveredPackage]:
        """
        Sort Djangospice applications by dependencies.

        Detects missing dependencies and circular dependencies.
        Preserves original discovery order when possible.
        """
        applications = [
            app for app in applications if app.enabled
        ]

        identifiers = {}

        for app in applications:
            identifiers[app.name] = app

            if app.is_djangospice:
                config = app.config

                for identifier in (
                    getattr(config, "app_key", None),
                    app.label,
                ):
                    if identifier:
                        identifiers[identifier] = app

        state = {}
        ordered = []
        stack = []

        def visit(app: DiscoveredPackage):
            name = app.name
            status = state.get(name, 0)

            if status == 2:
                return

            if status == 1:
                cycle = " -> ".join(
                    [*stack, name]
                )

                raise ImproperlyConfigured(
                    f"Circular application dependency: {cycle}"
                )

            state[name] = 1
            stack.append(name)

            if app.is_djangospice:
                dependencies = getattr(
                    app.config,
                    "app_dependencies",
                    (),
                )

                for dependency in dependencies:
                    identifier = self._dependency_identifier(
                        dependency
                    )

                    required = identifiers.get(identifier)

                    if required is None:
                        raise ImproperlyConfigured(
                            f"Application '{name}' requires "
                            f"'{identifier}', but it is not "
                            "registered or enabled."
                        )

                    visit(required)

            stack.pop()
            state[name] = 2
            ordered.append(app)

        for application in applications:
            visit(application)

        return ordered

    # ---------------------------------------------------------
    # Complete discovery
    # ---------------------------------------------------------

    def discover(self) -> list[DiscoveredPackage]:
        """
        Discover applications from all supported sources.

        Order:
            1. Built-in Djangospice applications.
            2. Project applications.
            3. Installed extensions.
            4. Explicit Djangospice applications.
            5. Ordinary explicit Django applications.
        """
        explicit = self.discover_explicit()

        ordinary = [
            app for app in explicit
            if not app.is_djangospice
        ]

        explicit_djangospice = [
            app for app in explicit
            if app.is_djangospice
        ]

        builtin = self.discover_builtin()
        project = self.discover_project()
        extensions = self.discover_extensions()

        # Framework applications always precede custom applications.
        framework = self.deduplicate(builtin)

        custom = self.deduplicate([
            *project,
            *extensions,
            *explicit_djangospice,
        ])

        # Resolve dependencies across the framework and custom apps.
        djangospice_apps = self.resolve_dependencies([
            *framework,
            *custom,
        ])

        # Ordinary Django applications retain their original order.
        result = self.deduplicate([
            *ordinary,
            *djangospice_apps,
        ])

        self._discovered = result

        return result

    # ---------------------------------------------------------
    # Django registration
    # ---------------------------------------------------------

    def build(self) -> list[str]:
        """
        Return the final INSTALLED_APPS list.

        This must run before django.setup().
        """
        applications = self.discover()

        return [
            application.entry
            for application in applications
        ]

    @property
    def applications(self) -> tuple[DiscoveredPackage, ...]:
        """Return the most recently discovered applications."""
        return tuple(self._discovered)
