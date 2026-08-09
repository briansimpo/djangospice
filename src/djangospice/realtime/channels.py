from typing import Any, Optional, Sequence
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .groups import build_group_name


def send_to_group(group_name: str, method_name: str, data: Any) -> None:
    """
    Synchronously dispatches a event message to a specific Django Channels group.

    Args:
        group_name (str): The exact name of the target Channels group.
        method_name (str): The name of the consumer method that will handle this event 
                            (maps to the 'type' key in the Channels payload).
        data (Any): The payload/message data to send to the group.

    Raises:
        RuntimeError: If the Django Channels layer is not configured or available.
    """
    channel_layer = get_channel_layer()
    
    if channel_layer is None:
        raise RuntimeError(
            "Django Channels layer is not configured. "
            "Verify CHANNEL_LAYERS is properly defined in your settings."
        )

    # Wrap the async group_send call to execute synchronously
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": method_name,
            "data": data,
        },
    )


def channel_broadcast(scope: str, method_name: str, data: Any, identifiers: Optional[Sequence[Any]] = None) -> None:
    """
    A convenience wrapper that builds a deterministic group name and 
    broadcasts a message to it.

    Args:
        scope (str): The functional domain or context of the channel (e.g., 'chat').
        method_name (str): The consumer method intended to handle this event.
        data (Any): The payload data to distribute.
        identifiers (Optional[Sequence[Any]], optional): Unique entity IDs used to isolate 
                                                         the group scope. Defaults to None.
    """
    # Deterministically derive the group name using the same system bounds
    group_name = build_group_name(scope=scope, identifiers=identifiers)

    send_to_group(
        group_name=group_name,
        method_name=method_name,
        data=data,
    )