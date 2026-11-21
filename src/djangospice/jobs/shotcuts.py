from typing import Any
from .handle import JobHandle


def dispatch_job(job) -> JobHandle:
    from .dispatcher import JobDispatcher
    return JobDispatcher.dispatch(job)


def report_job(job, current: int, total: int, message: str = "", **extra: Any) -> None:
    from .context import  active_reporter

    reporter = active_reporter.get()

    if reporter:
        reporter.progress(
            job=job,
            current=current,
            total=total,
            message=message,
            **extra,
        )
