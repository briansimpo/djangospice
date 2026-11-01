from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from importlib import import_module
from importlib.metadata import entry_points
from pathlib import Path
from typing import Iterable, Literal

from django.apps import AppConfig as DjangoAppConfig
from django.core.exceptions import ImproperlyConfigured
from djangospice.package.config import AppConfig as DjangospiceAppConfig


@dataclass(frozen=True)
class DiscoveredPackage:
    """A discovered Djangospice or standard Django application."""

    entry: str
    config: DjangoAppConfig
    source: Literal["builtin", "project", "extension"]

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
    Discover, validate, resolve and register Django applications using AST parsing
    to prevent premature module imports before settings are configured.

    Sources:
        - Built-in Djangospice applications.
        - Project-root applications.
        - Configured project application directories (e.g., apps/).
        - Installed Djangospice entry-point extensions.

    All discovery happens safely before django.setup().
    """

    ENTRY_POINT_GROUP = "djangospice"

    def __init__(
        self,
        project_dir: str | Path,
        app_directories: Iterable[str] = ("apps",),
        package_name: str = "djangospice",
    ) -> None:
        self.project_dir = Path(project_dir).resolve()
        self.app_directories = tuple(app_directories)
        self.package_name = package_name

        try:
            package = import_module(package_name)
        except ImportError as exc:
            raise ImproperlyConfigured(
                f"Could not import primary package '{package_name}': {exc}"
            ) from exc

        if not package.__file__:
            raise ImproperlyConfigured(
                f"Cannot locate package directory for '{package_name}'."
            )

        self.package_dir = Path(package.__file__).resolve().parent
        self._discovered: list[DiscoveredPackage] = []
        self._is_discovered: bool = False

    # ---------------------------------------------------------
    # General Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _is_private(path: Path) -> bool:
        return any(part.startswith("_") for part in path.parts)

    @staticmethod
    def _is_valid_package(directory: Path, root: Path, app_directories: tuple[str, ...] = ()) -> bool:
        """
        Check if a directory is a valid Python package structure.
        Container directories (like 'apps/') are allowed to lack __init__.py 
        if they are configured app roots.
        """
        try:
            relative = directory.relative_to(root)
        except ValueError:
            return False

        current = root
        parts = relative.parts

        for i, part in enumerate(parts):
            current /= part
            
            # If this part is a top-level container directory (e.g., 'apps'), 
            # it doesn't strictly need an __init__.py file.
            if i == 0 and part in app_directories:
                continue

            # Every actual app package and subpackage must have an __init__.py
            if not (current / "__init__.py").is_file():
                return False

        return True
    
    @staticmethod
    def _config_path(module_path: str, class_name: str) -> str:
        return f"{module_path}.{class_name}"

    def _is_internal(self, config: DjangoAppConfig) -> bool:
        return config.name == self.package_name or config.name.startswith(f"{self.package_name}.")

    # ---------------------------------------------------------
    # AST-Based Config Discovery
    # ---------------------------------------------------------

    def _discover_config_classes(self, apps_file: Path, module_path: str) -> list[str]:
        """
        Statically parse apps.py using Python's AST module to find configuration 
        classes without importing the module or executing any side-effects.
        """
        if not apps_file.is_file():
            return []

        try:
            tree = ast.parse(apps_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ImproperlyConfigured(
                f"Failed to parse application module file '{apps_file}': {exc}"
            ) from exc

        discovered = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Skip base DjangospiceAppConfig class if encountered in source definition
                if node.name in ("AppConfig", "DjangospiceAppConfig"):
                    continue

                # Check if it inherits from an AppConfig class or defines a 'name' attribute
                is_config_subclass = any(
                    (isinstance(base, ast.Name) and "AppConfig" in base.id) or
                    (isinstance(base, ast.Attribute) and "AppConfig" in base.attr)
                    for base in node.bases
                )
                has_name_assignment = any(
                    isinstance(stmt, ast.Assign) and
                    any(isinstance(target, ast.Name) and target.id == "name" for target in stmt.targets)
                    for stmt in node.body
                )

                if is_config_subclass or has_name_assignment:
                    discovered.append(self._config_path(module_path, node.name))

        return discovered

    # ---------------------------------------------------------
    # Discovery Sources
    # ---------------------------------------------------------

    def discover_builtin(self) -> list[DiscoveredPackage]:
        discovered = []
        if not self.package_dir.is_dir():
            return discovered

        for apps_file in sorted(self.package_dir.rglob("apps.py")):
            directory = apps_file.parent
            try:
                relative = directory.relative_to(self.package_dir)
            except ValueError:
                continue

            if self._is_private(relative) or not self._is_valid_package(directory, self.package_dir):
                continue

            module_path = ".".join((self.package_name, *relative.parts, "apps"))
            for entry in self._discover_config_classes(apps_file, module_path):
                discovered.append(
                    DiscoveredPackage(
                        entry=entry,
                        config=self._resolve(entry),
                        source="builtin",
                    )
                )
        return discovered

    def discover_project(self) -> list[DiscoveredPackage]:
        discovered = []
        visited: set[Path] = set()

        def process(apps_file: Path) -> None:
            directory = apps_file.parent
            if directory in visited:
                return
            visited.add(directory)

            try:
                relative = directory.relative_to(self.project_dir)
            except ValueError:
                return

            if not relative.parts or self._is_private(relative):
                return

            if relative.parts[0] == self.package_name:
                return

            if not self._is_valid_package(directory, self.project_dir, self.app_directories):
                return

            module_path = ".".join((*relative.parts, "apps"))
            for entry in self._discover_config_classes(apps_file, module_path):
                discovered.append(
                    DiscoveredPackage(
                        entry=entry,
                        config=self._resolve(entry),
                        source="project",
                    )
                )

        # 1. Project-root level apps
        if self.project_dir.is_dir():
            for directory in sorted(self.project_dir.iterdir()):
                if directory.is_dir() and not directory.name.startswith("_"):
                    apps_file = directory / "apps.py"
                    if apps_file.is_file():
                        process(apps_file)

        # 2. Nested app directories (e.g., apps/*)
        for app_directory in self.app_directories:
            root = (self.project_dir / app_directory).resolve()
            if not root.is_dir() or not self._is_valid_package(root, self.project_dir, self.app_directories):
                continue

            for apps_file in sorted(root.rglob("apps.py")):
                process(apps_file)

        return discovered

    def discover_extensions(self) -> list[DiscoveredPackage]:
        """Discover external extensions packaged via Python entry points."""
        discovered = []
        try:
            eps = entry_points()
            group_eps = eps.select(group=self.ENTRY_POINT_GROUP) if hasattr(eps, "select") else eps.get(self.ENTRY_POINT_GROUP, [])
        except Exception:
            return discovered

        for ep in group_eps:
            try:
                entry = ep.value
                config = self._resolve(entry)
                discovered.append(
                    DiscoveredPackage(
                        entry=entry,
                        config=config,
                        source="extension",
                    )
                )
            except Exception as exc:
                raise ImproperlyConfigured(
                    f"Failed to load entry point extension '{ep.name}': {exc}"
                ) from exc

        return discovered

    # ---------------------------------------------------------
    # Deduplication & Dependency Resolution
    # ---------------------------------------------------------

    def deduplicate(self, applications: list[DiscoveredPackage]) -> list[DiscoveredPackage]:
        result = []
        names: dict[str, DiscoveredPackage] = {}
        labels: dict[str, str] = {}

        for application in applications:
            config = application.config

            if config.name in names:
                continue

            existing_name = labels.get(config.label)
            if existing_name and existing_name != config.name:
                raise ImproperlyConfigured(
                    f"Duplicate Django application label '{config.label}': "
                    f"shared by '{existing_name}' and '{config.name}'."
                )

            names[config.name] = application
            labels[config.label] = config.name
            result.append(application)

        return result

    @staticmethod
    def _dependency_identifier(dependency: object) -> str:
        if isinstance(dependency, str):
            return dependency

        for attribute in ("app_key", "key", "name", "package"):
            value = getattr(dependency, attribute, None)
            if isinstance(value, str) and value.strip():
                return value.strip()

        raise ImproperlyConfigured(
            f"Invalid application dependency: {dependency!r}. "
            "Must be a string or expose app_key, key, name, or package."
        )

    def _resolve(self, entry: str) -> DjangoAppConfig:
        try:
            return DjangoAppConfig.create(entry)
        except Exception as exc:
            raise ImproperlyConfigured(
                f"Could not load Django application config '{entry}': {exc}"
            ) from exc

    def resolve_dependencies(self, applications: list[DiscoveredPackage]) -> list[DiscoveredPackage]:
        active_apps = [app for app in applications if app.enabled]
        identifiers: dict[str, DiscoveredPackage] = {}

        for app in active_apps:
            identifiers[app.name] = app
            if app.is_djangospice:
                config = app.config
                for identifier in (getattr(config, "app_key", None), app.label):
                    if identifier:
                        identifiers[identifier] = app

        state: dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited
        ordered: list[DiscoveredPackage] = []
        stack: list[str] = []

        def visit(app: DiscoveredPackage) -> None:
            name = app.name
            status = state.get(name, 0)

            if status == 2:
                return
            if status == 1:
                cycle = " -> ".join([*stack, name])
                raise ImproperlyConfigured(f"Circular application dependency detected: {cycle}")

            state[name] = 1
            stack.append(name)

            if app.is_djangospice:
                dependencies = getattr(app.config, "app_dependencies", ())
                for dependency in dependencies:
                    identifier = self._dependency_identifier(dependency)
                    required = identifiers.get(identifier)
                    if required is None:
                        raise ImproperlyConfigured(
                            f"Application '{name}' requires dependency '{identifier}', "
                            "but it is not registered or enabled."
                        )
                    visit(required)

            stack.pop()
            state[name] = 2
            ordered.append(app)

        for application in active_apps:
            visit(application)

        return ordered

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def discover(self) -> list[DiscoveredPackage]:
        """Execute full discovery, deduplication, and topological dependency sorting."""
        if self._is_discovered:
            return self._discovered

        builtin = self.discover_builtin()
        project = self.discover_project()
        extensions = self.discover_extensions()

        applications = self.deduplicate([
            *builtin,
            *project,
            *extensions,
        ])

        self._discovered = self.resolve_dependencies(applications)
        self._is_discovered = True
        return self._discovered

    def build(self) -> list[str]:
        """Return entry strings for all valid, sorted discovered applications."""
        return [app.entry for app in self.discover()]

    @property
    def applications(self) -> tuple[DiscoveredPackage, ...]:
        return tuple(self._discovered)