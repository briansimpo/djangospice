from __future__ import annotations

from typing import Any

from djangospice.core.serializer import serialize

from djangospice.core.payload import Payload
from djangospice.realtime import Broadcast



def get_payload(event: str, payload: Any = None) -> dict:
    if isinstance(payload, Payload):
        return payload.to_dict()

    return Payload(event=event, data=serialize(payload)).to_dict()


def broadcast_to_user(user_id: str, event: str, payload: Any = None):
    """
    Broadcast an event to a single user.
    """
    data = get_payload(event, payload)
    return Broadcast.user(user_id=str(user_id), data=data)


def broadcast_to_group(group_name: str, event: str, payload: Any = None):
    """
    Broadcast an event to a group.
    """
    data = get_payload(event, payload)
    return Broadcast.group(group_name=str(group_name), data=data)