
from dataclasses import dataclass
from typing import Any, Type

from djangospice.core.resolver import resolve_class
from .job import Job
from .result import JobResult


@dataclass
class Execution:
    job: Job

    @classmethod
    def construct(cls, job_path: str, payload: dict[str, Any]) -> "Execution":
        job_cls: Type[Job] = resolve_class(job_path)
        job = job_cls.from_dict(payload)
        return cls(job=job)

    def execute(self, task: Any) -> JobResult:
        from .worker import JobWorker 
        return JobWorker(task=task).execute(self.job)
