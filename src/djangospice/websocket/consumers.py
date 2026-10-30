import json
from typing import Any
from channels.generic.websocket import AsyncWebsocketConsumer

from .serializers import dumps     


class BaseConsumer(AsyncWebsocketConsumer):
    """Base asynchronous WebSocket consumer providing lifecycle hooks and serialization.

    This class serves as an abstract layer for handling structural WebSocket 
    operations like connection lifecycle, group subscription management, and 
    structured data transmission. It intentionally contains no business logic.

    Attributes:
        subscriptions (set[str]): Groups joined during the lifetime of this connection.
    """

    subscriptions: set[str]

    # ------------------------------------------------------------------
    # Connection Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Initializes the connection state and invokes the connection hook.

        Subclasses should normally override `on_connect()` instead of
        replacing this method entirely.
        """
        self.subscriptions = set()
        await self.on_connect()

    async def disconnect(self, close_code: int) -> None:
        """Cleans up all group subscriptions before invoking the disconnect hook.

        Args:
            close_code (int): The WebSocket close code provided by the client or server.
        """
        # Safely acquire subscriptions in case initialization failed prematurely
        active_subs = getattr(self, "subscriptions", set())
        for group in tuple(active_subs):
            await self.channel_layer.group_discard(group, self.channel_name)

        active_subs.clear()
        await self.on_disconnect(close_code)

    async def on_connect(self) -> None:
        """Hook executed after a WebSocket handshake is initiated.

        Subclasses should override this method to handle authentication,
        subscribe to initial groups, and explicitly call `await self.accept()`.
        """
        await self.accept()

    async def on_disconnect(self, close_code: int) -> None:
        """Hook executed during teardown after all group subscriptions are cleared.

        Args:
            close_code (int): The WebSocket close code.
        """
        pass

    # ------------------------------------------------------------------
    # Convenience Properties
    # ------------------------------------------------------------------

    @property
    def user(self) -> Any:
        """Retrieves the authenticated user from the Django Channels connection scope.

        Returns:
            Any: The user object if authenticated, otherwise AnonymousUser or None.
        """
        return self.scope.get("user")

    @property
    def session(self) -> Any:
        """Retrieves the session object from the Django Channels connection scope.

        Returns:
            Any: The session dictionary-like object if sessions are enabled, otherwise None.
        """
        return self.scope.get("session")

    # ------------------------------------------------------------------
    # Subscription Management
    # ------------------------------------------------------------------

    async def subscribe(self, group: str) -> None:
        """Subscribes this connection to a specific channel layer group.

        Args:
            group (str): The unique string name of the group to join.
        """
        if group in self.subscriptions:
            return

        self.subscriptions.add(group)
        await self.channel_layer.group_add(group, self.channel_name)

    async def unsubscribe(self, group: str) -> None:
        """Removes this connection from a specific channel layer group.

        Args:
            group (str): The unique string name of the group to leave.
        """
        if group not in self.subscriptions:
            return

        self.subscriptions.remove(group)
        await self.channel_layer.group_discard(group, self.channel_name)

    # ------------------------------------------------------------------
    # Data Transmission & Serialization
    # ------------------------------------------------------------------

    async def send_data(self, event: dict[str, Any] | Any) -> None:
        """Serializes and transmits data over the WebSocket connection.

        Intelligently extracts the inner payload from a Channels event dictionary 
        (expecting a 'data' key) or safely falls back to handling raw structures.

        Args:
            event (dict[str, Any] | Any): The event dictionary or raw data payload to send.
        """
        # Extract 'data' from the event dictionary if present; otherwise use the event itself
        data = event.get("data", event) if isinstance(event, dict) else event

        if isinstance(data, (dict, list)):
            json_data = dumps(data)
            await self.send(text_data=json_data)

        elif isinstance(data, str):
            await self.send(text_data=data)

        elif isinstance(data, (bytes, bytearray)):
            await self.send(bytes_data=data)
            
        else:
            # Fallback to string representation to prevent silently dropping data
            await self.send(text_data=str(data))

    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        """Handles incoming raw WebSocket data frames.

        Attempts to parse incoming text frames as JSON. If parsing fails, passes 
        the raw string down to `receive_data`. Binary frames are passed as raw bytes.

        Args:
            text_data (str | None): Incoming raw text frame payload. Defaults to None.
            bytes_data (bytes | None): Incoming raw binary frame payload. Defaults to None.
        """
        if text_data:
            try:
                payload = json.loads(text_data)
            except json.JSONDecodeError:
                payload = text_data

            await self.receive_data(payload)
            
        elif bytes_data:
            await self.receive_data(bytes_data)

    async def receive_data(self, data: Any) -> None:
        """Hook to handle parsed or raw incoming WebSocket payloads.

        Subclasses should override this method to implement incoming message business logic.

        Args:
            data (Any): Parsed JSON (dict/list), raw string, or raw bytes data.
        """
        pass
    
    # ------------------------------------------------------------------
    # Channel Layer Broadcast Handlers
    # ------------------------------------------------------------------

    async def broadcast_message(self, event: dict[str, Any]) -> None:
        """Handles 'broadcast_message' typed events dispatched via `group_send`.

        Args:
            event (dict[str, Any]): The channel layer event payload map.
        """
        await self.send_data(event)

    async def user_message(self, event: dict[str, Any]) -> None:
        """Handles 'user_message' typed events dispatched via `group_send`.

        Args:
            event (dict[str, Any]): The channel layer event payload map.
        """
        await self.send_data(event)

    async def group_message(self, event: dict[str, Any]) -> None:
        """Handles 'group_message' typed events dispatched via `group_send`.

        Args:
            event (dict[str, Any]): The channel layer event payload map.
        """
        await self.send_data(event)
        
