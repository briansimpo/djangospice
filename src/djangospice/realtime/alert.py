from typing import Union

from djangospice.core.payload import Payload
from .broadcast import Broadcast


class Alert:

    @classmethod
    def _get_user_id(cls, user_or_id: Union[int, object]) -> int:
        """Extract the primary key from a model instance or primitive ID."""
        return getattr(
            user_or_id,
            "pk",
            getattr(user_or_id, "id", user_or_id),
        )

    @classmethod
    def send(cls, user_or_id: Union[int, object], message: str, level: str = "info") -> None:
        payload = Payload(
            type="alert",
            alert=Payload(message=message,level=level).to_dict(),
        ).to_dict()

        Broadcast.user(
            user=cls._get_user_id(user_or_id),
            data=payload,
        )

    @classmethod
    def success(cls, user_or_id, message: str) -> None:
        cls.send(user_or_id, message, "success")

    @classmethod
    def error(cls, user_or_id, message: str) -> None:
        cls.send(user_or_id, message, "error")

    @classmethod
    def warning(cls, user_or_id, message: str) -> None:
        cls.send(user_or_id, message, "warning")

    @classmethod
    def info(cls, user_or_id, message: str) -> None:
        cls.send(user_or_id, message, "info")