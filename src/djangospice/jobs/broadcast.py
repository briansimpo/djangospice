from typing import Any

from djangospice.realtime.broadcast import Broadcast

from .events import JobEvent


def broadcast_event(event: JobEvent, data: dict[str, Any] | None = None) -> None:

    job = event.job

    if not job.id:
        return

    payload = {
        "type": str(event),
        "job": job.to_dict(),
        **(data or {}),
    }

    Broadcast.group(
        group=f"job_{job.id}",
        data=payload,
    )

    if job.user_id:
        Broadcast.user(
            user=job.user_id,
            data=payload,
        )