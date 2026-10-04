from __future__ import annotations
from importlib.metadata import PackageNotFoundError, version as package_version
from collections.abc import Mapping
from typing import Any

from django.apps import apps

from .config import AppConfig 

from .metadata import Dependency, Metadata, Permission


class AppDiscovery:
    """Discover Django apps that declare Djangospice metadata."""

    def discover(self) -> tuple[Metadata, ...]:
        """Discover metadata for all registered Djangospice apps."""

        discovered: list[Metadata] = []

        for config in apps.get_app_configs():
            metadata = self.metadata_from_config(config)
            if metadata is not None:
                discovered.append(metadata)

        return tuple(discovered)

    def discover_one(
        self,
        config: AppConfig,
    ) -> Metadata | None:
        """Discover metadata for one app config or Django app label."""
        return self.metadata_from_config(config)

    def discover_many(
        self,
        configs: tuple[AppConfig | str, ...] | list[AppConfig | str] | None = None,
    ) -> tuple[Metadata, ...]:
        """Discover metadata for multiple app configs or labels."""

        if configs is None:
            return self.discover()

        discovered: list[Metadata] = []

        for config in configs:
            metadata = self.discover_one(config)
            if metadata is not None:
                discovered.append(metadata)

        return tuple(discovered)

    def metadata_from_config(
        self,
        config: AppConfig,
    ) -> Metadata | None:
        """Build metadata from an app configuration."""

        # Only apps explicitly opting into Djangospice are discovered.
        raw_key = getattr(config, "app_key", None)
        if not isinstance(raw_key, str) or not raw_key.strip():
            return None

        key = raw_key.strip()

        raw_package = getattr(config, "app_package", None)
        declared_package = (
            raw_package.strip()
            if isinstance(raw_package, str) and raw_package.strip()
            else None
        )

        # Local project apps may not have a Python distribution.
        package = declared_package or config.name

        raw_version = getattr(config, "app_version", None)
        declared_version = (
            raw_version.strip()
            if isinstance(raw_version, str) and raw_version.strip()
            else None
        )

        if declared_version:
            version = declared_version
        elif declared_package:
            version = self._distribution_version(declared_package)
            if version is None:
                raise ValueError(
                    f"App {key!r} declares package {declared_package!r}, "
                    "but no app_version or installed distribution version "
                    "could be determined."
                )
        else:
            version = "0.0.0"

        return Metadata.from_values(
            key=key,
            name=(
                getattr(config, "app_name", None)
                or config.verbose_name
                or config.label
            ),
            package=package,
            version=version,
            description=getattr(config, "app_description", "") or "",
            author=getattr(config, "app_author", "") or "",
            icon=getattr(config, "app_icon", "") or "",
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
    def _distribution_version(package: str | None) -> str | None:
        """Return an installed distribution version when available."""

        if not isinstance(package, str) or not package.strip():
            return None

        try:
            return package_version(package.strip())
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
                    version_specifier=str(spec or ""),
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
                        "Dependency declaration requires 'key': "
                        f"{dependency!r}"
                    )

                result.append(
                    Dependency(
                        key=str(dependency["key"]),
                        version_specifier=str(
                            dependency.get("version_specifier")
                            or dependency.get("version")
                            or ""
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
                        "Permission declarations require 'codename' "
                        f"and 'name': {permission!r}"
                    )

                result.append(
                    Permission(
                        codename=str(permission["codename"]),
                        name=str(permission["name"]),
                        description=str(permission.get("description") or ""),
                    )
                )

            elif isinstance(permission, (tuple, list)) and len(permission) >= 2:
                result.append(
                    Permission(
                        codename=str(permission[0]),
                        name=str(permission[1]),
                        description=(
                            str(permission[2] or "")
                            if len(permission) >= 3
                            else ""
                        ),
                    )
                )

            else:
                raise TypeError(
                    f"Unsupported permission declaration: {permission!r}"
                )

        return tuple(result)