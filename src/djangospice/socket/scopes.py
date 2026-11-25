from django.db import models


class ChannelScope(models.TextChoices):
    EVERYONE = "everyone", "Everyone"
    USER = "user", "User"
    GROUP = "group", "Group"
    CHANNEL = "channel", "Channel"