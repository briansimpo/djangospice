from __future__ import annotations

from collections.abc import Iterable, Sequence

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from .exceptions import (
    AppDependencyError,
    AppNotRegistered,
    AppStateError,
)
from .models import (
    AppDependency,
    AppInstance,
    AppInstallation,
    AppAction,
    AppStatus,
)
from .metadata import Metadata
from .permissions import permission_sync


class AppRegistry:
    """Persistent registry for Djangospice application metadata and state."""

    # ------------------------------------------------------------------
    # Registration and lookup
    # ------------------------------------------------------------------

    @transaction.atomic
    def register(self, metadata: Metadata) -> AppInstance:
        """Register an application or refresh its declared metadata.

        Registration does not install the package and does not change the
        existing application's lifecycle state.
        """
        app, created = AppInstance.objects.get_or_create(
            key=metadata.key,
            defaults={
                **self._metadata_defaults(metadata),
                "status": AppStatus.DISCOVERED,
                "enabled": False,
            },
        )

        app = AppInstance.objects.select_for_update().get(pk=app.pk)

        self._validate_identity(app, metadata)

        if not created:
            self._apply_metadata(app, metadata)

        permission_sync.sync(app, metadata.permissions)
        self._sync_dependencies(app, metadata.dependencies)

        return app

    def register_many(
        self,
        metadata: Iterable[Metadata],
    ) -> list[AppInstance]:
        """Register multiple applications atomically."""
        with transaction.atomic():
            return [self.register(item) for item in metadata]

    @classmethod
    def get(cl, key: str) -> AppInstance:
        try:
            return AppInstance.objects.get(key=key)
        except AppInstance.DoesNotExist as exc:
            raise AppNotRegistered(
                f"Application '{key}' is not registered."
            ) from exc

    @classmethod
    def get_by_app_label(cls, app_label: str) -> AppInstance:
        try:
            return AppInstance.objects.get(app_label=app_label)
        except AppInstance.DoesNotExist as exc:
            raise AppNotRegistered(
                f"No registered application has app label '{app_label}'."
            ) from exc

    @classmethod
    def exists(cls, key: str) -> bool:
        return AppInstance.objects.filter(key=key).exists()

    @classmethod
    def all(cls) -> QuerySet[AppInstance]:
        return AppInstance.objects.all()

    @classmethod
    def installed(cls) -> QuerySet[AppInstance]:
        return cls.all().filter(status=AppStatus.INSTALLED)

    @classmethod
    def enabled(cls) -> QuerySet[AppInstance]:
        return cls.installed().filter(enabled=True)

    @classmethod
    def permissions(cls, key: str):
        """Return the Django permission records declared by an application."""
        app = cls.get(key)
        return app.permission_records.select_related("permission").all()

    # ------------------------------------------------------------------
    # Dependencies
    # ------------------------------------------------------------------

    def dependencies(
        self,
        key: str,
        *,
        include_optional: bool = True,
    ) -> QuerySet[AppDependency]:
        app = self.get(key)
        queryset = app.dependencies.select_related("app")

        if not include_optional:
            queryset = queryset.filter(optional=False)

        return queryset

    def dependents(self, key: str) -> QuerySet[AppDependency]:
        """Return dependency declarations that refer to the given app."""
        return AppDependency.objects.filter(
            dependency_key=key,
        ).select_related("app")

    def providers(self, capability: str) -> QuerySet[AppInstance]:
        return AppInstance.objects.filter(
            capabilities__key=capability,
            status=AppStatus.INSTALLED,
            enabled=True,
        ).distinct()

    # ------------------------------------------------------------------
    # Enable and disable
    # ------------------------------------------------------------------

    @transaction.atomic
    def enable(self, key: str) -> AppInstance:
        app = self._locked_app(key)

        if app.status == AppStatus.DISABLED:
            app.status = AppStatus.INSTALLED
        elif app.status != AppStatus.INSTALLED:
            raise AppStateError(
                f"Cannot enable '{key}' from status '{app.status}'."
            )

        app.enabled = True
        app.save(update_fields=("enabled", "status"))

        self._record(app, AppAction.ENABLE, successful=True)
        return app

    @transaction.atomic
    def disable(self, key: str) -> AppInstance:
        app = self._locked_app(key)

        if app.status != AppStatus.INSTALLED:
            raise AppStateError(
                f"Cannot disable '{key}' from status '{app.status}'."
            )

        app.enabled = False
        app.status = AppStatus.DISABLED
        app.save(update_fields=("enabled", "status"))

        self._record(app, AppAction.DISABLE, successful=True)
        return app

    # ------------------------------------------------------------------
    # Installation lifecycle
    # ------------------------------------------------------------------

    @transaction.atomic
    def begin_install(self, key: str) -> AppInstallation:
        app = self._locked_app(key)

        if app.status in {
            AppStatus.INSTALLING,
            AppStatus.UPDATING,
            AppStatus.UNINSTALLING,
        }:
            raise AppStateError(
                f"Cannot begin installation of '{key}' while its status "
                f"is '{app.status}'."
            )

        if app.status == AppStatus.INSTALLED:
            raise AppStateError(
                f"Application '{key}' is already installed; use begin_update()."
            )

        app.status = AppStatus.INSTALLING
        app.enabled = False
        app.last_error = ""
        app.save(
            update_fields=("status", "enabled", "last_error")
        )

        return self._record(app, AppAction.INSTALL, successful=False)

    @transaction.atomic
    def complete_install(self, key: str) -> AppInstance:
        app = self._locked_app(key)
        self._require_status(app, key, AppStatus.INSTALLING)

        app.status = AppStatus.INSTALLED
        app.enabled = True
        app.last_error = ""
        app.save(
            update_fields=(
                "status",
                "enabled",
                "last_error",
            )
        )

        self._complete_latest(app, AppAction.INSTALL, successful=True)
        return app

    @transaction.atomic
    def fail_install(
        self,
        key: str,
        error: Exception | str,
    ) -> AppInstance:
        app = self._locked_app(key)
        self._require_status(app, key, AppStatus.INSTALLING)

        message = str(error)
        app.status = AppStatus.FAILED
        app.enabled = False
        app.last_error = message
        app.save(
            update_fields=("status", "enabled", "last_error")
        )

        self._complete_latest(
            app,
            AppAction.INSTALL,
            successful=False,
            error=message,
        )
        return app

    # ------------------------------------------------------------------
    # Update lifecycle
    # ------------------------------------------------------------------

    @transaction.atomic
    def begin_update(self, key: str) -> AppInstallation:
        app = self._locked_app(key)

        if app.status != AppStatus.INSTALLED or not app.enabled:
            raise AppStateError(
                f"Cannot update '{key}' from status '{app.status}' "
                "or while it is disabled."
            )

        app.status = AppStatus.UPDATING
        app.save(update_fields=("status"))

        return self._record(app, AppAction.UPDATE, successful=False)

    @transaction.atomic
    def complete_update(
        self,
        key: str,
        metadata: Metadata,
    ) -> AppInstance:
        app = self._locked_app(key)
        self._require_status(app, key, AppStatus.UPDATING)
        self._validate_identity(app, metadata)

        self._apply_metadata(app, metadata)
        app.status = AppStatus.INSTALLED
        app.enabled = True
        app.last_error = ""
        app.save()

        permission_sync.sync(app, metadata.permissions)
        self._sync_dependencies(app, metadata.dependencies)

        self._complete_latest(app, AppAction.UPDATE, successful=True)
        return app

    @transaction.atomic
    def fail_update(
        self,
        key: str,
        error: Exception | str,
    ) -> AppInstance:
        app = self._locked_app(key)
        self._require_status(app, key, AppStatus.UPDATING)

        message = str(error)
        app.status = AppStatus.INSTALLED
        app.last_error = message
        app.save(update_fields=("status", "last_error"))

        self._complete_latest(
            app,
            AppAction.UPDATE,
            successful=False,
            error=message,
        )
        return app

    # ------------------------------------------------------------------
    # Unregistration
    # ------------------------------------------------------------------

    @transaction.atomic
    def unregister(self, key: str, *, force: bool = False) -> None:
        """Remove an app's registry record.

        This does not uninstall its Python package or remove its Django app
        from INSTALLED_APPS.
        """
        app = self._locked_app(key)

        dependents = list(
            self.dependents(key).exclude(app_id=app.pk)
        )

        if dependents and not force:
            names = ", ".join(sorted({item.app.key for item in dependents}))
            raise AppDependencyError(
                f"Cannot unregister '{key}'; required by: {names}."
            )

        if app.status in {
            AppStatus.INSTALLING,
            AppStatus.UPDATING,
            AppStatus.UNINSTALLING,
        }:
            raise AppStateError(
                f"Cannot unregister '{key}' while its status is '{app.status}'."
            )

        # Forced unregistration removes references that would otherwise
        # point to an application no longer present in the registry.
        if force:
            AppDependency.objects.filter(dependency_key=key).delete()

        permission_sync.remove(app)
        app.delete()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _metadata_defaults(metadata: Metadata) -> dict:
        return {
            "name": metadata.name,
            "app_label": metadata.app_label or metadata.key,
            "package": metadata.package or "",
            "version": metadata.version or  "",
            "django_app": metadata.django_app or "",
            "description": metadata.description or "",
            "author": metadata.author or "",
            "url": metadata.url or "",
            "icon": metadata.icon or "",
            "homepage": metadata.homepage or "",
        }

    @staticmethod
    def _apply_metadata(app: AppInstance, metadata: Metadata) -> None:
        for field, value in AppRegistry._metadata_defaults(metadata).items():
            setattr(app, field, value)

    @staticmethod
    def _validate_identity(app: AppInstance, metadata: Metadata) -> None:
        if app.key != metadata.key:
            raise AppStateError("Metadata key does not match the registered app.")

        if app.package != metadata.package:
            raise AppStateError(
                f"Application key '{metadata.key}' is already registered "
                f"for package '{app.package}'."
            )

        expected_label = metadata.app_label or metadata.key
        if app.app_label != expected_label:
            raise AppStateError(
                f"Application '{metadata.key}' is already registered with "
                f"app label '{app.app_label}'."
            )

    def _locked_app(self, key: str) -> AppInstance:
        try:
            return AppInstance.objects.select_for_update().get(key=key)
        except AppInstance.DoesNotExist as exc:
            raise AppNotRegistered(
                f"Application '{key}' is not registered."
            ) from exc

    @staticmethod
    def _require_status(
        app: AppInstance,
        key: str,
        expected: str,
    ) -> None:
        if app.status != expected:
            raise AppStateError(
                f"Application '{key}' must have status '{expected}', "
                f"not '{app.status}'."
            )

    def _sync_dependencies(
        self,
        app: AppInstance,
        dependencies: Sequence,
    ) -> None:
        desired = {item.key: item for item in dependencies}

        if app.key in desired:
            raise AppDependencyError(
                f"Application '{app.key}' cannot depend on itself."
            )

        existing = {
            item.dependency_key: item
            for item in app.dependencies.all()
        }

        for dependency_key, dependency in desired.items():
            AppDependency.objects.update_or_create(
                app=app,
                dependency_key=dependency_key,
                defaults={
                    "version_specifier": dependency.version_specifier,
                    "optional": dependency.optional,
                },
            )

        stale = set(existing) - set(desired)
        if stale:
            app.dependencies.filter(dependency_key__in=stale).delete()

    @staticmethod
    def _record(
        app: AppInstance,
        action: str,
        *,
        successful: bool,
        error: str = "",
    ) -> AppInstallation:
        now = timezone.now()

        return AppInstallation.objects.create(
            app=app,
            version=app.version,
            action=action,
            successful=successful,
            started_at=now,
            completed_at=now if successful else None,
            error=error,
        )

    def _complete_latest(
        self,
        app: AppInstance,
        action: str,
        *,
        successful: bool,
        error: str = "",
    ) -> None:
        record = (
            app.installation_history
            .select_for_update()
            .filter(action=action, completed_at__isnull=True)
            .order_by("-started_at")
            .first()
        )

        if record is None:
            self._record(
                app,
                action,
                successful=successful,
                error=error,
            )
            return

        record.successful = successful
        record.completed_at = timezone.now()
        record.error = error
        record.save(
            update_fields=(
                "successful",
                "completed_at",
                "error",
            )
        )
