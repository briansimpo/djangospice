from django.contrib.auth.models import AbstractUser

from djangospice.notification.base import BaseNotification
from djangospice.notification.enums import Channel
from djangospice.notification.models import NotificationPreference
from djangospice.notification.registry import ChannelRegistry


class ChannelService:
    """
    Resolves the final notification channels by combining:
        Notification.channels(user)
            ∩
        User Preferences
            ∩
        Installed Providers
    """

    @classmethod
    def preferences(cls,user: AbstractUser, category: str | None = None) -> tuple[Channel, ...]:
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

        # Category overrides (wins over global)
        if category:
            for preference in preferences:
                if preference.category == category:
                    enabled[Channel(preference.channel)] = preference.enabled

        return tuple(channel for channel, value in enabled.items() if value)

    @classmethod
    def channels(cls, user: AbstractUser, notification: BaseNotification) -> tuple[Channel, ...]:
        supported = set(notification.channels(user))

        # Critical notifications bypass user preferences.
        if notification.required:
            preferred = supported
        else:
            preferred = set(
                cls.preferences(user=user, category=notification.category)
            )

        installed = set(ChannelRegistry.channels())

        # The intersection determines the final delivery channels
        return tuple(supported & preferred & installed)
