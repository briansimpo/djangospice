from dataclasses import dataclass, field
from typing import Any
from djangospice.events import BaseEvent
from djangospice.jobs import Job

@dataclass
class JobQueuedEvent(BaseEvent):
    job: Job

@dataclass
class JobStartedEvent(BaseEvent):
    job: Job

@dataclass
class JobProgressedEvent(BaseEvent):
    job: Job
    current: int
    total: int
    message: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

@dataclass
class JobCompletedEvent(BaseEvent):
    job: Job
    result: Any = None

@dataclass
class JobFailedEvent(BaseEvent):
    job: Job
    exception: Exception