from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


@dataclass(frozen=True, slots=True)
class Permission:
    codename: str
    name: str
    description: str = ""

    def __post_init__(self) -> None:
        if not self.codename.strip():
            raise ValueError("Permission codename cannot be empty.")
        if not self.name.strip():
            raise ValueError("Permission name cannot be empty.")

    def qualified(self, app_key: str) -> str:
        """Return the Djangospice-qualified permission identifier."""
        return f"{app_key}.{self.codename}"


@dataclass(frozen=True, slots=True)
class Dependency:
    key: str
    version_specifier: str = ""
    optional: bool = False

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("Dependency key cannot be empty.")


@dataclass(frozen=True, slots=True)
class Metadata:
    """Immutable snapshot of Django app configuration and package metadata."""

    # Djangospice identity
    key: str

    # Django AppConfig information
    name: str
    django_app: str
    app_label: str

    # Python distribution/package information
    package: str
    version: str

    # Additional Djangospice metadata
    description: str = ""
    author: str = ""
    icon: str | None = None
    url: str | None = None
    homepage: str | None = None

    # Ecosystem declarations
    dependencies: tuple[Dependency, ...] = field(default_factory=tuple)
    permissions: tuple[Permission, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for field_name in (
            "key",
            "name",
            "django_app",
            "app_label",
            "package",
            "version",
        ):
            value = getattr(self, field_name)
            if not value or not value.strip():
                raise ValueError(
                    f"Metadata field '{field_name}' cannot be empty."
                )

        permission_codenames = [
            permission.codename for permission in self.permissions
        ]
        if len(permission_codenames) != len(set(permission_codenames)):
            raise ValueError("Duplicate permission codenames are not allowed.")

        dependency_keys = [dependency.key for dependency in self.dependencies]
        if len(dependency_keys) != len(set(dependency_keys)):
            raise ValueError("Duplicate dependency keys are not allowed.")

    @property
    def namespace(self) -> str:
        return self.key

    @classmethod
    def from_config(cls, config: object) -> Metadata:
        """Build metadata from a AppConfig instance."""
        return cls(
            key=config.app_key,
            name=config.verbose_name,
            django_app=config.name,
            app_label=config.label,
            package=config.app_package or config.name,
            version=config.app_version,
            description=config.app_description,
            author=config.app_author,
            icon=config.app_icon,
            url=config.app_url,
            homepage=config.app_homepage,
            dependencies=tuple(config.app_dependencies),
            permissions=tuple(config.app_permissions),
        )

    @classmethod
    def from_values(
        cls,
        key: str,
        name: str,
        package: str,
        version: str,
        django_app: str,
        app_label: str,
        description: str = "",
        author: str = "",
        icon: str | None = None,
        url: str | None = None,
        homepage: str | None = None,
        dependencies: Iterable[Dependency] | Mapping[str, str] = (),
        permissions: Iterable[
            Permission | Mapping[str, str] | tuple[str, str]
        ] = (),
    ) -> Metadata:
        if isinstance(dependencies, Mapping):
            normalized_dependencies = tuple(
                Dependency(key=k, version_specifier=v)
                for k, v in dependencies.items()
            )
        else:
            normalized_dependencies = tuple(dependencies)

        normalized_permissions: list[Permission] = []
        seen_permissions: set[str] = set()

        for declaration in permissions:
            if isinstance(declaration, Permission):
                permission = declaration
            elif isinstance(declaration, Mapping):
                permission = Permission(
                    codename=str(declaration["codename"]),
                    name=str(declaration["name"]),
                    description=str(declaration.get("description", "")),
                )
            elif isinstance(declaration, tuple) and len(declaration) in (2, 3):
                permission = Permission(
                    codename=str(declaration[0]),
                    name=str(declaration[1]),
                    description=(
                        str(declaration[2]) if len(declaration) == 3 else ""
                    ),
                )
            else:
                raise TypeError(
                    f"Unsupported permission declaration: {declaration!r}"
                )

            if permission.codename in seen_permissions:
                raise ValueError(
                    f"Duplicate permission codename: {permission.codename}"
                )

            seen_permissions.add(permission.codename)
            normalized_permissions.append(permission)

        return cls(
            key=key.strip(),
            name=name.strip(),
            django_app=django_app.strip(),
            app_label=app_label.strip(),
            package=package.strip(),
            version=version.strip(),
            description=description.strip(),
            author=author.strip(),
            icon=icon,
            url=url,
            homepage=homepage,
            dependencies=normalized_dependencies,
            permissions=tuple(normalized_permissions),
        )