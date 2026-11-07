from django.conf import settings
from django.db import models
from django.utils import timezone

from djangospice.db.models import BaseModel
from djangospice.notification.enums import ActionStatus
from .notification import Notification


class NotificationAction(BaseModel):
    """An executable action attached to a notification."""

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="actions",
    )

    # Action definition
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=2048)

    label = models.CharField(max_length=100)
    icon = models.CharField(max_length=100, blank=True)
    method = models.CharField(max_length=10, choices=[("get", "GET"), ("post", "POST")], default="get")
    style = models.CharField(max_length=20, default="primary")
    attributes = models.JSONField(default=dict, blank=True)

    # Execution state
    status = models.CharField(
        max_length=20,
        choices=ActionStatus.choices,
        default=ActionStatus.PENDING,
        db_index=True,
    )

    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_notification_actions",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("notification", "name"),
                name="unique_notification_action",
            ),
        ]

    def mark_as_completed(self, user=None, result=None):
        self.status = ActionStatus.COMPLETED
        self.completed_by = user
        self.completed_at = timezone.now()
        self.result = result

        self.save(
            update_fields=[
                "status",
                "completed_by",
                "completed_at",
                "result",
            ]
        )

    @property
    def is_completed(self):
        return self.status == ActionStatus.COMPLETED
