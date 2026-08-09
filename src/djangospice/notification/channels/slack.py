import logging
from typing import Any

from django.contrib.auth.models import AbstractUser

from djangospice.notification.channels import NotificationChannel
from djangospice.notification.enums import Channel
from djangospice.notification.messages import SlackMessage
from djangospice.notification.models import Notification


logger = logging.getLogger(__name__)


class SlackChannel(NotificationChannel[SlackMessage]):
    """Delivers notifications via Slack."""

    channel = Channel.SLACK

    def send(self, user: AbstractUser, notification: Notification) -> dict[str, Any] | None:
        message = self.message(notification)

        if not message:
            return None

        # TODO: Implement Slack Block Kit / Webhook integration
        logger.info("Slack -> user=%s", user.pk)
        return {"user": user.pk}

