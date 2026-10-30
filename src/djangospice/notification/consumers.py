from djangospice.websocket.consumers import BaseConsumer
from djangospice.websocket.groups import build_group_name
from djangospice.websocket.scopes import ChannelScope


class NotificationConsumer(BaseConsumer):
    """Deliver real-time notifications to the authenticated user."""

    async def on_connect(self) -> None:
        user = self.user

        if not user or not user.is_authenticated:
            await self.close()
            return

        group_name = build_group_name(ChannelScope.USER, [f"notification_user_{user.pk}"])

        await self.subscribe(group_name)
        await self.accept()
