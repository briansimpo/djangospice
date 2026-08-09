import logging
from typing import Any

from django.contrib.auth.models import AbstractUser

from djangospice.notification.channels import NotificationChannel
from djangospice.notification.enums import Channel
from djangospice.notification.messages import SmsMessage
from djangospice.notification.models import Notification


logger = logging.getLogger(__name__)


class SMSChannel(NotificationChannel[SmsMessage]):
    """Delivers notifications via SMS."""

    channel = Channel.SMS

    def send(self, user: AbstractUser, notification: Notification) -> dict[str, Any] | None:
        message = self.message(notification)
        phone = getattr(user, "phone_number", None)

        if not message or not phone:
            return None

        # TODO: Replace with actual SMS provider integration (Twilio, AWS SNS, etc.)
        logger.info("SMS %s -> %s", phone, message.body)
        return {"phone": phone}

