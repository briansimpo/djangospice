from djangospice.realtime.broadcast import Broadcast


def broadcast_job_event(job, event_type: str, extra_data: dict = None) -> None:
    """
    Pipes job execution updates directly to our high-level Broadcast service.
    """
    if not getattr(job, "id", None):
        return

    payload = {
        "job_id": job.id,
        "job_class": job.__class__.__name__,
        **(extra_data or {}),
    }

    # 1. Broadcast to the job-specific group (e.g., clients watching a single import task)
    Broadcast.event(
        event=f"job.{event_type}",
        data=payload,
        group=f"job_{job.id}"
    )

    # 2. Broadcast to the user-specific feed if a user is attached to the job
    if hasattr(job, "user") and job.user:
        Broadcast.event(
            event=f"job.{event_type}",
            data=payload,
            user=job.user
        )