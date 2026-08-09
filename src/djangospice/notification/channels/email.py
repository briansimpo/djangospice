import logging
from typing import Any

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.mail import EmailMultiAlternatives

from djangospice.notification.channels import NotificationChannel
from djangospice.notification.enums import Channel
from djangospice.notification.messages import EmailMessage
from djangospice.notification.models import Notification


logger = logging.getLogger(__name__)


class EmailChannel(NotificationChannel[EmailMessage]):
    """Delivers notifications via Email."""

    channel = Channel.EMAIL

    def send(self, user: AbstractUser, notification: Notification) -> dict[str, Any] | None:
        message = self.message(notification)

        if not message or not user.email:
            return None

        email = EmailMultiAlternatives(
            subject=message.subject,
            body=message.text,
            from_email=message.from_email or settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            cc=message.cc,
            bcc=message.bcc,
            reply_to=message.reply_to,
            headers=message.headers,
        )

        if message.html:
            email.attach_alternative(message.html, "text/html")

        for attachment in message.attachments:
            email.attach(*attachment)

        email.send()
        return {"email": user.email}

