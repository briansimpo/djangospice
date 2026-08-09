from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from djangospice.database.models import BaseModel
from djangospice.notification.enums import Channel


class NotificationPreference(BaseModel):
    """
    Stores user opt-in/opt-out preferences for specific notification categories and channels.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="notification_preferences")
    category = models.CharField(max_length=255,blank=True, null=True, help_text="The notification category (e.g., 'marketing'). If null, applies globally to the channel.")
    channel = models.CharField(max_length=100, choices=Channel.choices)
    enabled = models.BooleanField(default=True, help_text="Whether the user wants to receive these notifications.")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "category", "channel"],
                name="uniq_notification_preference",
            )
        ]
        indexes = [
            models.Index(fields=["user", "category"]),
        ]

    def __str__(self) -> str:
        category_label = self.category if self.category else "Global"
        status = "Enabled" if self.enabled else "Disabled"
        return f"{self.user} | {category_label} via {self.channel} ({status})"

