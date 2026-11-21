
import logging
from typing import Any

from celery.exceptions import Retry

from .job import Job
from .enums import JobStatus
from .result import JobResult
from .reporter import JobReporter
from .context import  active_reporter

logger = logging.getLogger(__name__)


class JobWorker:
    """
    Executes jobs and coordinates their execution lifecycle.

    This is the single authority for job execution, retries,
    and lifecycle reporting.
    """

    def __init__(self, task: Any = None) -> None:
        self.task = task

    def execute(self, job: Job) -> JobResult:
        # Establish execution identifier.
        job._id = (
            self.task.request.id
            if self.task
            else (job.id or "sync-execution")
        )

        reporter = JobReporter(self.task)
        token = active_reporter.set(reporter)

        reporter.started(job)

        try:
            result = job.handle()

            if not isinstance(result, JobResult):
                result = JobResult(result)

            reporter.completed(job, result)

            return result

        except Retry:
            # Celery retry is a control-flow exception.
            # Do not report it as a final failure.
            raise

        except Exception as exc:
            if self._should_retry(job, exc):
                retries = self.task.request.retries
                countdown = self._get_countdown(job, retries)

                job.status = JobStatus.RETRYING.value

                logger.warning(
                    "Job %s [%s] failed. "
                    "Retrying (%s/%s) in %ss.",
                    job.name,
                    job.id,
                    retries + 1,
                    job.max_retries,
                    countdown,
                )

                reporter.retrying(
                    job,
                    exception=exc,
                    countdown=countdown,
                )

                raise self.task.retry(
                    exc=exc,
                    max_retries=job.max_retries,
                    countdown=countdown,
                )

            reporter.failed(job, exception=exc)
            raise

        finally:
            active_reporter.reset(token)

    def _should_retry(self, job: Job, exc: Exception) -> bool:
        if not self.task:
            return False

        if job.max_retries <= 0:
            return False

        retry_on = job.retry_on

        if not retry_on:
            return False

        if not isinstance(exc, retry_on):
            return False

        return self.task.request.retries < job.max_retries

    @staticmethod
    def _get_countdown(job: Job, retries: int) -> int:
        if job.retry_backoff <= 0:
            return 0

        return job.retry_backoff * (2 ** retries)
