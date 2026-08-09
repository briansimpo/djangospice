from typing import Any
from django.utils import timezone
from django.db import models
from django.utils.translation import gettext_lazy as _


from djangospice.database.models import BaseModel
from djangospice.notification.enums import Channel, DeliveryStatus

from .notification import Notification



class NotificationDelivery(BaseModel):
    """
    Tracks the delivery lifecycle of a notification through a
    specific delivery channel.
    """

    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="deliveries",)
    channel = models.CharField(max_length=100, choices=Channel.choices)
    status = models.CharField(max_length=50, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING,)
    provider = models.CharField(max_length=255,blank=True,null=True,help_text="The provider used (Twilio, SendGrid, FCM, etc.).",)

    # Retry State
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=5)

    # Timestamps
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)
    last_attempt_at = models.DateTimeField(blank=True, null=True)

    # Diagnostics
    error = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["channel", "status"]),
            models.Index(fields=["notification", "channel"]),
        ]

    def __str__(self) -> str:
        return f"{self.notification_id} [{self.channel}] {self.status}"


    def is_pending(self) -> bool:
        return self.status == DeliveryStatus.PENDING

    def is_processing(self) -> bool:
        return self.status == DeliveryStatus.PROCESSING

    def is_failed(self) -> bool:
        return self.status == DeliveryStatus.FAILED

    def is_sent(self) -> bool:
        # Hierarchical state: if it's delivered or read, it was definitely sent.
        return self.status in {
            DeliveryStatus.SENT,
            DeliveryStatus.DELIVERED,
            DeliveryStatus.READ,
        }

    def is_delivered(self) -> bool:
        return self.status in {
            DeliveryStatus.DELIVERED,
            DeliveryStatus.READ,
        }

    def is_read(self) -> bool:
        return self.status == DeliveryStatus.READ

    def can_retry(self) -> bool:
        """Determine whether another delivery attempt is allowed."""
        return (
            self.status == DeliveryStatus.FAILED 
            and self.attempts < self.max_attempts
        )

    def mark_processing(self) -> None:
        self.status = DeliveryStatus.PROCESSING
        self.attempts += 1
        self.last_attempt_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "attempts",
                "last_attempt_at",
            ]
        )

    def mark_sent(self, metadata: dict[str, Any] | None = None) -> None:
        self.status = DeliveryStatus.SENT
        self.sent_at = timezone.now()

        if metadata:
            self.metadata = self.metadata or {}
            self.metadata |= metadata

        self.save(
            update_fields=[
                "status",
                "sent_at",
                "metadata",
            ]
        )

    def mark_delivered(self, metadata: dict[str, Any] | None = None) -> None:
        self.status = DeliveryStatus.DELIVERED
        self.delivered_at = timezone.now()

        if metadata:
            self.metadata = self.metadata or {}
            self.metadata |= metadata

        self.save(
            update_fields=[
                "status",
                "delivered_at",
                "metadata",
            ]
        )

    def mark_read(self) -> None:
        self.status = DeliveryStatus.READ
        self.read_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "read_at",
            ]
        )

    def mark_failed(self, error: str | Exception, metadata: dict[str, Any] | None = None) -> None:
        self.status = DeliveryStatus.FAILED
        self.error = str(error)

        if metadata:
            self.metadata = self.metadata or {}
            self.metadata |= metadata

        self.save(
            update_fields=[
                "status",
                "error",
                "metadata",
            ]
        )

    def mark_cancelled(self) -> None:
        self.status = DeliveryStatus.CANCELLED
        self.save(update_fields=["status"])

    def add_metadata(self, **kwargs: Any) -> None:
        self.metadata = self.metadata or {}
        self.metadata |= kwargs

        self.save(update_fields=["metadata"])

    def clear_error(self) -> None:
        self.error = ""
        self.save(update_fields=["error"])