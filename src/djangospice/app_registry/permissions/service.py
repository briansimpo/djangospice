from __future__ import annotations

from django.contrib.auth.models import Permission
from django.db.models import Q, QuerySet

from djangospice.app_registry.models import AppStatus, AppInstance
from djangospice.app_registry.exceptions import AppNotRegistered

from .default import APP_ACCESS


class AppAccess:
    """Resolve application access using Django user/group permissions."""

    def __init__(self, user) -> None:
        self.user = user

    @property
    def is_authenticated(self) -> bool:
        return bool(self.user and self.user.is_authenticated)

    def apps(self) -> QuerySet[AppInstance]:
        queryset = AppInstance.objects.filter(
            enabled=True,
        )
        if not self.is_authenticated:
            return queryset.none()
        if self.user.is_superuser:
            return queryset

        return queryset.filter(
            permission_records__codename=APP_ACCESS.codename,
        ).filter(
            Q(permission_records__permission__group__user=self.user)
            | Q(permission_records__permission__user=self.user)
        ).distinct()

    def all(self) -> QuerySet[AppInstance]:
        return self.apps()

    def has_app(self, app: str | AppInstance) -> bool:
        if not self.is_authenticated:
            return False
        if self.user.is_superuser:
            return True
        installed = self._resolve_app(app)
        if not installed.enabled or installed.status != AppStatus.INSTALLED:
            return False
        return self.user.has_perm(f"{installed.app_label}.{APP_ACCESS.codename}")

    def permissions(self, app: str | AppInstance) -> QuerySet[Permission]:
        installed = self._resolve_app(app)
        if not self.is_authenticated:
            return Permission.objects.none()

        queryset = Permission.objects.filter(
            app_permission__app=installed,
        )
        if self.user.is_superuser:
            return queryset

        return queryset.filter(
            Q(group__user=self.user) | Q(user=self.user),
        ).distinct()

    def has_permission(self, app: str | AppInstance, permission: str) -> bool:
        if not self.is_authenticated:
            return False
        installed = self._resolve_app(app)
        codename = permission.removeprefix(f"{installed.app_label}.")
        return bool(
            self.user.is_superuser
            or self.user.has_perm(f"{installed.app_label}.{codename}")
        )

    def _resolve_app(self, app: str | AppInstance) -> AppInstance:
        if isinstance(app, AppInstance):
            return app
        try:
            return AppInstance.objects.get(key=app)
        except AppInstance.DoesNotExist:
            raise AppNotRegistered(f"AppInstance '{app}' is not registered.") from None

