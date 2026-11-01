
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from djangospice.core.serializable import Serializable

from .helpers import get_app_label
from .handle import JobHandle
from .enums import JobStatus
from .result import JobResult
from .context import active_reporter


logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class Job(Serializable):
    """Base executable execution unit."""

    user_id: Any | None = None
    queue: str = "default"
    retries: int = 0
    backoff: int = 0
    timeout: int | float | None = None

    _id: str | None = None
    status: JobStatus = JobStatus.QUEUED
    current: int = 0
    total: int = 0

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        explicit_name = cls.__dict__.get("name")

        if not explicit_name:
            app_label = get_app_label(cls.__module__)
            cls.name = f"{app_label}.{cls.__name__}"
        else:
            cls.name = explicit_name

    @property
    def id(self) -> str | None:
        """Read-only access to the job execution identifier."""
        return self._id

    @property
    def percent(self) -> float:
        """Real-time progress percentage."""
        if not self.total:
            return 0.0

        return round((self.current / self.total) * 100, 2)

    def dispatch(
        self,
        queue: str | None = None,
        *,
        seconds: int | float = 0,
        minutes: int | float = 0,
        hours: int | float = 0,
    ) -> JobHandle:
        from .dispatcher import JobDispatcher

        return JobDispatcher.dispatch(
            self,
            queue=queue or self.queue,
            seconds=seconds,
            minutes=minutes,
            hours=hours,
        )

    def dispatch_now(self) -> JobResult:
        from .worker import JobWorker

        return JobWorker(task=None).execute(self)

    def progress(
        self,
        current: int,
        total: int,
        message: str = "",
        **extra: Any,
    ) -> None:
        self.current = current
        self.total = total
        self.status = JobStatus.PROGRESS

        reporter = active_reporter.get()

        if reporter:
            reporter.progress(
                self,
                current=current,
                total=total,
                message=message,
                **extra,
            )

    def handle(self) -> Any:
        raise NotImplementedError(
            "Jobs must implement their own handle() method."
        )
