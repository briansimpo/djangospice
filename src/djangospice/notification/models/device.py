from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from djangospice.database.models import BaseModel
from djangospice.notification.enums import Platform


class NotificationDevice(BaseModel):
    """
    Registered push notification device.

    A user may register multiple devices (phone, tablet,
    browser, desktop, etc.).

    Tokens are managed by the client application and are used
    by push providers (FCM, APNs, etc.) to deliver notifications.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_devices")
    platform = models.CharField(max_length=20, choices=Platform.choices)
    token = models.TextField(unique=True, help_text="FCM/APNs/Web Push device token.")
    device_id = models.CharField(max_length=255,blank=True, null=True, help_text="Application-specific device identifier.")
    device_name = models.CharField(max_length=255,blank=True, null=True, help_text="Friendly device name (e.g. Brian's iPhone).")
    app_name = models.CharField(max_length=100, blank=True, null=True)
    app_version = models.CharField(max_length=50, blank=True, null=True)
    os_version = models.CharField(max_length=100,blank=True,null=True)
    language = models.CharField(max_length=20, blank=True, null=True)
    timezone = models.CharField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=True, help_text="Whether this device can receive notifications.")
    last_seen_at = models.DateTimeField(blank=True,null=True)
    last_notified_at = models.DateTimeField(blank=True,null=True)

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["user", "token"],
                name="uniq_user_device_token",
            )
        ]
        ordering = (
            "-last_seen_at",
            "-created",
        )

        indexes = [
            models.Index(
                fields=[
                    "user",
                    "active",
                ]
            ),
            models.Index(
                fields=[
                    "platform",
                    "active",
                ]
            ),
        ]

    def __str__(self):

        return (
            f"{self.user} "
            f"({self.platform})"
        )

    @property
    def is_mobile(self):
        return self.platform in (
            Platform.ANDROID,
            Platform.IOS,
        )

    @property
    def is_web(self):
        return self.platform == Platform.WEB

    @property
    def is_desktop(self):
        return self.platform == Platform.WINDOWS
