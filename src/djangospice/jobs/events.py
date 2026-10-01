from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from djangospice.events import BaseEvent

from .base import Job


@dataclass(frozen=True, slots=True)
class JobEvent(BaseEvent):
    """Base event for job lifecycle events."""
    job: Job


@dataclass(frozen=True, slots=True)
class JobQueued(JobEvent):
    name = "job_queued"


@dataclass(frozen=True, slots=True)
class JobStarted(JobEvent):
    name = "job_started"


@dataclass(frozen=True, slots=True)
class JobProgressed(JobEvent):
    name = "job_progressed"
    message: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class JobCompleted(JobEvent):
    name = "job_completed"
    result: Any = None


@dataclass(frozen=True, slots=True)
class JobFailed(JobEvent):
    name = "job_failed"
    error: str = ""