from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from djangospice.core.serializable import Serializable
from djangospice.core.resolver import get_app_label

from .shotcuts import dispatch_job, report_job
from .handle import JobHandle
from .enums import JobStatus


@dataclass(kw_only=True)
class Job(Serializable):
    """Base executable execution unit."""
    
    retry_on: ClassVar[tuple[type[Exception], ...]] = (Exception,)
    max_retries: ClassVar[int] = 3
    retry_backoff: ClassVar[int] = 60

    _id: str | None = None
    user_id: Any | None = None
    status: str = JobStatus.QUEUED
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

    def dispatch(self) -> JobHandle:
        return  dispatch_job(self)

    def progress(self, current: int, total: int, message: str = "", **extra: Any) -> None:
        report_job(job=self, current=current, total=total, message=message, **extra)

    def handle(self) -> Any:
        raise NotImplementedError("Jobs must implement their own handle() method.")

    def to_status(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": str(self.status),
            "current": self.current,
            "total": self.total,
            "percent": self.percent,
        }
