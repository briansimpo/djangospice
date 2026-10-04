from __future__ import annotations

from collections.abc import Mapping
from importlib.metadata import PackageNotFoundError, version as package_version
from typing import Any

from django.apps import apps

from .config import DjangospiceConfig
from .metadata import Dependency, Metadata, Permission


class DjangoAppDiscovery:
    """Discover and normalize Djangospice application metadata."""

    def __init__(self, app_registry=None) -> None:
        self.app_registry = app_registry or apps

    def discover(self) -> tuple[Metadata, ...]:
        """Discover all registered Django apps declaring an app_key."""
        discovered: list[Metadata] = []

        for config in self.app_registry.get_app_configs():
            metadata = self.metadata_from_config(config)
            if metadata is not None:
                discovered.append(metadata)

        return tuple(discovered)

    def metadata_from_config(self, config: DjangospiceConfig) -> Metadata | None:
        """Build normalized metadata from a Djangospice configuration."""
        key = getattr(config, "app_key", None)

        if not isinstance(key, str) or not key.strip():
            return None

        key = key.strip()
        package = (
            getattr(config, "app_package", None) or config.name
        ).strip()

        if not package:
            raise ValueError(
                f"Djangospice app '{key}' must declare a valid app_package."
            )

        version = (
            getattr(config, "app_version", None)
            or self._distribution_version(package)
        )

        if not isinstance(version, str) or not version.strip():
            raise ValueError(
                f"Djangospice app '{key}' must declare app_version because "
                f"the distribution version for '{package}' could not be determined."
            )

        return Metadata.from_values(
            key=key,
            name=(
                getattr(config, "app_name", None)
                or config.verbose_name
                or config.label
            ),
            package=package,
            version=version.strip(),
            description=getattr(config, "app_description", "") or "",
            author=getattr(config, "app_author", "") or "",
            icon=getattr(config, "app_icon", None) or "",
            url=getattr(config, "app_url", None),
            homepage=getattr(config, "app_homepage", None),
            django_app=config.name,
            app_label=config.label,
            dependencies=self._dependencies(
                getattr(config, "app_dependencies", ())
            ),
            permissions=self._permissions(
                getattr(config, "app_permissions", ())
            ),
        )

    @staticmethod
    def _distribution_version(package: str) -> str | None:
        """Return the installed distribution version, if available."""
        try:
            return package_version(package)
        except PackageNotFoundError:
            return None

    @staticmethod
    def _dependencies(value: Any) -> tuple[Dependency, ...]:
        """Normalize supported dependency declaration formats."""
        if not value:
            return ()

        if isinstance(value, Mapping):
            return tuple(
                Dependency(
                    key=str(key),
                    version_specifier=str(spec),
                )
                for key, spec in value.items()
            )

        result: list[Dependency] = []

        for dependency in value:
            if isinstance(dependency, Dependency):
                result.append(dependency)

            elif isinstance(dependency, str):
                result.append(Dependency(key=dependency))

            elif isinstance(dependency, Mapping):
                if "key" not in dependency:
                    raise ValueError(
                        f"Dependency declaration requires 'key': {dependency!r}"
                    )

                result.append(
                    Dependency(
                        key=str(dependency["key"]),
                        version_specifier=str(
                            dependency.get("version_specifier")
                            or dependency.get("version", "")
                        ),
                        optional=bool(dependency.get("optional", False)),
                    )
                )

            else:
                raise TypeError(
                    f"Unsupported dependency declaration: {dependency!r}"
                )

        return tuple(result)

    @staticmethod
    def _permissions(value: Any) -> tuple[Permission, ...]:
        """Normalize supported permission declaration formats."""
        if not value:
            return ()

        result: list[Permission] = []

        for permission in value:
            if isinstance(permission, Permission):
                result.append(permission)

            elif isinstance(permission, Mapping):
                if "codename" not in permission or "name" not in permission:
                    raise ValueError(
                        "Permission declarations require 'codename' and 'name': "
                        f"{permission!r}"
                    )

                result.append(
                    Permission(
                        codename=str(permission["codename"]),
                        name=str(permission["name"]),
                        description=str(permission.get("description", "")),
                    )
                )

            elif isinstance(permission, (tuple, list)) and len(permission) >= 2:
                result.append(
                    Permission(
                        codename=str(permission[0]),
                        name=str(permission[1]),
                        description=(
                            str(permission[2]) if len(permission) >= 3 else ""
                        ),
                    )
                )

            else:
                raise TypeError(
                    f"Unsupported permission declaration: {permission!r}"
                )

        return tuple(result)