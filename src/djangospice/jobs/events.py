
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from djangospice.events import BaseEvent


@dataclass
class JobEvent(BaseEvent):
    """Base event for job lifecycle events."""

    job: Any


@dataclass
class JobQueued(JobEvent):
    name = "job_queued"


@dataclass
class JobStarted(JobEvent):
    name = "job_started"


@dataclass
class JobProgressed(JobEvent):
    name = "job_progressed"

    message: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class JobCompleted(JobEvent):
    name = "job_completed"

    result: Any = None


@dataclass
class JobFailed(JobEvent):
    name = "job_failed"

    error: str = ""
