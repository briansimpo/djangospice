from __future__ import annotations

from .registry import NotificationRegistry


def actionable(notification_klass):
    NotificationRegistry.register(notification_klass)
    return notification_klass
