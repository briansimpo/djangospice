from __future__ import annotations

from django.db import models
from django.contrib.auth.models import Permission
from djangospice.db.models import BaseModel


class AppStatus(models.TextChoices):
    DISCOVERED = "discovered", "Discovered"
    INSTALLING = "installing", "Installing"
    INSTALLED = "installed", "Installed"
    UPDATING = "updating", "Updating"
    FAILED = "failed", "Failed"
    DISABLED = "disabled", "Disabled"
    UNINSTALLING = "uninstalling", "Uninstalling"


class AppAction(models.TextChoices):
    REGISTER = "register", "Register"
    INSTALL = "install", "Install"
    UPDATE = "update", "Update"
    ENABLE = "enable", "Enable"
    DISABLE = "disable", "Disable"
    UNINSTALL = "uninstall", "Uninstall"
    ROLLBACK = "rollback", "Rollback"


class AppInstance(BaseModel):
    key = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    app_label = models.CharField(max_length=100, blank=True, null=True)
    package = models.CharField(max_length=255,blank=True, null=True)
    version = models.CharField(max_length=100, blank=True, null=True)

    django_app = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    icon = models.CharField(max_length=200, blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)
    homepage = models.URLField(blank=True, null=True)

    status = models.CharField(max_length=30, choices=AppStatus.choices, default=AppStatus.DISCOVERED)
    enabled = models.BooleanField(default=True)
    last_error = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ("key",)
        indexes = [
            models.Index(fields=("status",)),
            models.Index(fields=("enabled",)),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.version})"

    @property
    def is_installed(self) -> bool:
        return self.status == AppStatus.INSTALLED


class AppDependency(BaseModel):
    app = models.ForeignKey(
        AppInstance,
        on_delete=models.CASCADE,
        related_name="dependencies",
    )
    dependency_key = models.CharField(max_length=100)
    version_specifier = models.CharField(max_length=100, blank=True)
    optional = models.BooleanField(default=False)

    class Meta:
        ordering = ("dependency_key",)
        constraints = [
            models.UniqueConstraint(
                fields=("app", "dependency_key"),
                name="unique_app_dependency",
            )
        ]

    def __str__(self) -> str:
        return f"{self.app.key} -> {self.dependency_key} {self.version_specifier}".strip()


class AppInstallation(BaseModel):
    app = models.ForeignKey(
        AppInstance,
        on_delete=models.CASCADE,
        related_name="installation_history",
    )
    version = models.CharField(max_length=100)
    action = models.CharField(max_length=30, choices=AppAction.choices)
    successful = models.BooleanField(default=False)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ("-started_at",)

    def __str__(self) -> str:
        return f"{self.app.key} {self.action} {self.version}"


class AppPermission(BaseModel):
    """Registry record connecting an app declaration to Django Permission."""
    app = models.ForeignKey(
        AppInstance,
        on_delete=models.CASCADE,
        related_name="permission_records",
    )
    permission = models.OneToOneField(
        Permission,
        on_delete=models.CASCADE,
        related_name="app_permission",
    )
 
    class Meta:
        ordering = ("app__key", "permission__codename")
        constraints = [
            models.UniqueConstraint(
                fields=("app", "permission"),
                name="unique_app_permission",
            ),
        ]

    @property
    def qualified_name(self) -> str:
        return f"{self.app.key}.{self.permission.codename}"
