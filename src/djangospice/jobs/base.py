from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from djangospice.apps.utils import get_app_label
from djangospice.core.serializable import Serializable
from .handle import JobHandle
from .enums import JobStatus
from .result import JobResult
from .dispatcher import JobDispatcher
from .reporter import active_reporter

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class Job(Serializable):
    """
    Base executable execution unit.
    """
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

        # Automatically assign class path name if not explicitly set
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
        """The real-time progress percentage calculated from state."""
        if not self.total:
            return 0.0
        return round((self.current / self.total) * 100, 2)

    def dispatch(
        self,
        queue: str | None = None,
        *,
        seconds: int | float = 0,
        minutes: int | float = 0,
        hours: int | float = 0
    ) -> JobHandle:
        """
        Schedules the job for execution. Delays are keyword-only to 
        preserve immediate routing ergonomics.
        """
        if queue is None:
            queue = self.queue
        return JobDispatcher.dispatch(
            self, 
            queue=queue, 
            seconds=seconds, 
            minutes=minutes, 
            hours=hours
        )

    def dispatch_now(self) -> JobResult:
        from .worker import JobWorker
        return JobWorker(task=None).execute(self)

    def progress(self, current: int, total: int, message: str = "", **extra) -> None:
        """
        Pushes real-time progress updates through the active reporter context.
        """
        self.current = current
        self.total = total
        self.status = JobStatus.PROGRESS

        reporter = active_reporter.get()
        if reporter:
            reporter.progress(self, current=current, total=total, message=message, **extra)

    def handle(self) -> Any:
        raise NotImplementedError("Jobs must implement their own handle() method.")