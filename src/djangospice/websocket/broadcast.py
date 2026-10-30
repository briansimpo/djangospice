from __future__ import annotations

from typing import Any

from .channels import channel_broadcast
from .scopes import ChannelScope


class Broadcast:
    """
    High-level realtime messaging service.

    This service provides a stable API for publishing events to
    connected clients. The underlying transport (Channels, Redis,
    NATS, Kafka, SSE, etc.) is handled via `channel_broadcast`.
    
    All djangospice modules should use this service to dispatch realtime updates.
    """

    # ------------------------------------------------------------------
    # Core Transports
    # ------------------------------------------------------------------

    @classmethod
    def everyone(cls, data: Any, method_name: str = "broadcast_message") -> None:
        """
        Sends a message to EVERYONE currently connected.
        """
        channel_broadcast(
            scope=ChannelScope.EVERYONE,
            method_name=method_name,
            data=data,
        )

    @classmethod
    def user(cls, user: Any, data: Any, method_name: str = "user_message") -> None:
        """
        Sends a message to a specific user. 
        Automatically resolves the user ID if a model instance is passed.
        """
        user_id = getattr(user, "pk", user)
        channel_broadcast(
            scope=ChannelScope.USER,
            method_name=method_name,
            data=data,
            identifiers=[user_id],
        )

    @classmethod
    def group(cls, group: str, data: Any, method_name: str = "group_message") -> None:
        """
        Sends a message to a specific group/role (e.g., all 'admins').
        """
        channel_broadcast(
            scope=ChannelScope.GROUP,
            method_name=method_name,
            data=data,
            identifiers=[group],
        )
        
    @classmethod
    def channel(cls, channel: str, data: Any, method_name: str = "channel_message") -> None:
        """
        Sends a message to a specific channel.
        """
        channel_broadcast(
            scope=ChannelScope.CHANNEL,
            method_name=method_name,
            data=data,
            identifiers=[channel],
        )

    # ------------------------------------------------------------------
    # Routing & High-Level Wrappers
    # ------------------------------------------------------------------

    @classmethod
    def send(cls, data: Any, user: Any = None, group: str | None = None, channel: str | None = None) -> None:
        """
        Broadcast data to one or more specific destinations.
        """
        if user is not None:
            cls.user(user=user, data=data)

        if group is not None:
            cls.group(group=group, data=data)
            
        if channel is not None:
            cls.channel(channel=channel, data=data)

    @classmethod
    def event(cls, event: str, data: dict[str, Any] | None = None, user: Any = None, group: str | None = None, channel: str | None = None) -> None:
        """
        Wraps data in a standard event payload and dispatches it.
        """
        payload = {
            "event": event,
            "data": data or {},
        }

        cls.send(
            data=payload,
            user=user,
            group=group,
            channel=channel
        )

    # ------------------------------------------------------------------
    # Presence
    # ------------------------------------------------------------------

    @classmethod
    def online(cls, user: Any) -> None:
        """
        Dispatches an online presence event.
        """
        cls.user(
            user=user,
            data={"event": "presence.online"},
        )

    @classmethod
    def offline(cls, user: Any) -> None:
        """
        Dispatches an offline presence event.
        """
        cls.user(
            user=user,
            data={"event": "presence.offline"},
        )