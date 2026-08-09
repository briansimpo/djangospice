from django.shortcuts import get_object_or_404
from django.contrib.auth.models import AnonymousUser
from django.db.models import QuerySet


class NotificationService:
    """
    Application service for notification operations.

    Responsible for querying and manipulating notifications.
    Contains no UI or rendering logic.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def is_authenticated(user) -> bool:
        return bool(user and getattr(user, 'is_authenticated', False) and not isinstance(user, AnonymousUser))

    @classmethod
    def queryset(cls, user) -> QuerySet:
        """Returns the base queryset, ensuring the user is authenticated."""
        if not cls.is_authenticated(user):
            from djangospice.notification.models import Notification  # Avoid circular imports if models.py imports this service
            return Notification.objects.none()

        return user.notifications.all()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @classmethod
    def all(cls, user) -> QuerySet:
        return cls.queryset(user)

    @classmethod
    def unread(cls, user) -> QuerySet:
        # DRY: Rely on the base queryset and custom manager method
        return cls.queryset(user).unread().order_by("-timestamp")

    @classmethod
    def read(cls, user) -> QuerySet:
        return cls.queryset(user).read()

    @classmethod
    def latest(cls, user, limit: int = 10) -> QuerySet:
        return cls.queryset(user).order_by("-timestamp")[:limit]

    @classmethod
    def unread_count(cls, user) -> int:
        # DRY: Reuse the unread() query rather than repeating auth checks
        return cls.unread(user).count()

    @classmethod
    def get(cls, user, notification_id):
        # DRY: Passing the queryset directly to get_object_or_404 enforces 
        # both authentication and the recipient=user constraint automatically.
        return get_object_or_404(cls.queryset(user), id=notification_id)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    @classmethod
    def mark_as_read(cls, user, notification_id):
        notification = cls.get(user, notification_id)
        notification.mark_as_read()
        return notification

    @classmethod
    def mark_as_unread(cls, user, notification_id):
        notification = cls.get(user, notification_id)
        notification.mark_as_unread()
        return notification

    @classmethod
    def mark_all_as_read(cls, user) -> None:
        if not cls.is_authenticated(user):
            return

        notification_ids = list(cls.unread(user).values_list("pk", flat=True))
        
        if not notification_ids:
            return 

        user.notifications.mark_all_as_read()
        

    @classmethod
    def delete(cls, user, notification_id) -> None:
        notification = cls.get(user, notification_id)
        notification.mark_as_deleted()