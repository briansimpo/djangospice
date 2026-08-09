import logging
from typing import Any
from celery.exceptions import Retry

from .base import Job
from .enums import JobStatus
from .result import JobResult
from .reporter import JobReporter, active_reporter

logger = logging.getLogger(__name__)


class JobWorker:
    """Orchestrates job execution and delegates state tracking to the JobReporter."""

    def __init__(self, task: Any = None) -> None:
        self.task = task

    def execute(self, job: Job) -> JobResult:
        # 1. Establish initial system identifier
        job._id = self.task.request.id if self.task else (job.id or "sync-execution")

        # 2. Attach context reporter
        reporter = JobReporter(self.task)
        token = active_reporter.set(reporter)

        # Let the reporter kick off the lifecycle
        reporter.started(job)

        try:
            # 3. Execute business logic
            result = job.handle()

            # Normalize return values
            if not isinstance(result, JobResult):
                result = JobResult(value=result)

            # Let the reporter finalize completion
            reporter.completed(job, result=result)
            return result

        except Exception as exc:
            # A. Let Celery's built-in Retry bubble up cleanly
            if self.task and isinstance(exc, Retry):
                raise

            # B. Check for automatic retry threshold
            if self.task and job.retries > 0:
                retries_attempted = self.task.request.retries
                
                if retries_attempted < job.retries:
                    job.status = JobStatus.RETRY
                    countdown = job.backoff * (2**retries_attempted) if job.backoff > 0 else 0
                    
                    logger.warning(
                        f"Job {job.name} [{job.id}] failed. "
                        f"Retrying ({retries_attempted + 1}/{job.retries}) in {countdown}s..."
                    )
                    raise self.task.retry(exc=exc, countdown=countdown)

            # C. Register hard failure via the reporter
            reporter.failed(job, exception=exc)
            raise

        finally:
            active_reporter.reset(token)