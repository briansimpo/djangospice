
from django.contrib.auth.models import AbstractUser

from djangospice.notification.base import Notification
from djangospice.notification.enums import Channel
from djangospice.notification.models import NotificationPreference


class ChannelService:
    """
    Resolves final notification channels by combining:

        Notification.channels(user)
            ∩
        User Preferences (when configured)
            ∩
        Installed Providers

    Rules:
        - No preferences: use all supported channels.
        - Category preferences override global preferences.
        - Required notifications bypass user preferences.
        - Unsupported channels are always excluded.
    """

    @classmethod
    def preferences(cls, user: AbstractUser, category: str | None = None) -> tuple[Channel, ...]:

        categories = [None]
        if category:
            categories.append(category)

        preferences = NotificationPreference.objects.filter(
            user=user,
            category__in=categories,
        )

        enabled: dict[Channel, bool] = {}

        # Global preferences
        for preference in preferences:
            if preference.category is None:
                enabled[Channel(preference.channel)] = preference.enabled

        # Category overrides
        if category:
            for preference in preferences:
                if preference.category == category:
                    enabled[Channel(preference.channel)] = preference.enabled

        return tuple(
            channel
            for channel, value in enabled.items()
            if value
        )

    @classmethod
    def channels(cls, user: AbstractUser, notification: Notification) -> tuple[Channel, ...]:

        supported = tuple(notification.channels(user))

        # Required notifications bypass user preferences.
        if notification.required:
            return supported

        # No configured preferences: use supported channels.
        if not NotificationPreference.objects.filter(user=user).exists():
            return supported

        preferred = set(
            cls.preferences(
                user=user,
                category=notification.category,
            )
        )

        return tuple(
            channel for channel in supported
            if channel in preferred
        )
