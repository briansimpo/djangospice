from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def notify_user(user_id, notification = None) -> None:
    async_to_sync(get_channel_layer().group_send)(
        f"notifications_user_{user_id}",
        {
            "type": "notification_message",
            "data": {
                "id": "notification-123",
                "title": "Payment received",
                "message": "Your payment was processed.",
                "level": "success",
            },
        },
    )