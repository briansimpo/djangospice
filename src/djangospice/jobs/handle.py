from __future__ import annotations

from typing import Any
from celery.result import AsyncResult
from djangospice.core.serializer import deserialize

from .enums import JobStatus
from .result import JobResult


class JobHandle:
    """
    A unified, read-only wrapper representing a dispatched background job.
    Safely encapsulates the Celery AsyncResult and standardizes interaction.
    """
    __slots__ = ("_job_id", "_async_result")

    def __init__(self, job_id: str) -> None:
        self._job_id = job_id
        self._async_result: AsyncResult | None = None

    @property
    def id(self) -> str:
        """The unique identifier of the dispatched job."""
        return self._job_id

    @property
    def _result(self) -> AsyncResult:
        """Lazily instantiates the Celery AsyncResult backend on access."""
        if self._async_result is None:
            self._async_result = AsyncResult(self._job_id)
        return self._async_result

    @property
    def status(self) -> JobStatus:
        """
        Retrieves the current state of the job from the backend,
        mapping Celery states to our localized JobStatus.
        """
        celery_state = self._result.state
        
        # Celery internal states mapping to unified JobStatus
        mapping = {
            "PENDING": JobStatus.QUEUED,
            "STARTED": JobStatus.STARTED,
            "PROGRESS": JobStatus.PROGRESS,
            "SUCCESS": JobStatus.SUCCESS,
            "FAILURE": JobStatus.FAILURE,
            "RETRY": JobStatus.RETRY,
            "REVOKED": JobStatus.FAILURE,
        }
        return mapping.get(celery_state, JobStatus.QUEUED)

    @property
    def is_queued(self) -> bool:
        """Returns True if the job is waiting in the queue to be picked up."""
        return self.status == JobStatus.QUEUED

    @property
    def is_running(self) -> bool:
        """Returns True if the job is currently processing or reporting progress."""
        return self.status in (JobStatus.STARTED, JobStatus.PROGRESS)

    @property
    def is_done(self) -> bool:
        """Returns True if the job has finished running (regardless of success or failure)."""
        return self.status in (JobStatus.SUCCESS, JobStatus.FAILURE)

    @property
    def is_successful(self) -> bool:
        """Returns True if the job completed successfully without errors."""
        return self.status == JobStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        """Returns True if the job failed during execution or was forcefully revoked."""
        return self.status == JobStatus.FAILURE

    @property
    def is_retrying(self) -> bool:
        """Returns True if the job failed but is scheduled to retry."""
        return self.status == JobStatus.RETRY

    @property
    def progress_info(self) -> dict[str, Any] | None:
        """
        Safely extracts custom progress metadata if the job is actively executing.
        Returns None if no progress is currently reported.
        """
        if self.status == JobStatus.PROGRESS:
            info = self._result.info
            if isinstance(info, dict):
                return info
        return None

    @property
    def result(self) -> Any | None:
        """
        Attempts to retrieve the resolved result value immediately without blocking.
        Returns None if the job has not completed successfully yet.
        """
        if not self.is_successful:
            return None
        return self._deserialize_payload(self._result.result)

    @property
    def traceback(self) -> str | None:
        """
        Retrieves the exception traceback string if the job failed.
        Returns None if the job succeeded or is still running.
        """
        if self.is_failed:
            return self._result.traceback
        return None

    def abort(self, terminate: bool = True, signal: str = "SIGTERM") -> None:
        """
        Cancels the job execution. If already running, forcefully terminates the worker thread/process.
        """
        self._result.revoke(terminate=terminate, signal=signal)

    def wait(self, timeout: float | None = None, propagate: bool = True) -> Any:
        """
        Blocks synchronously until the job completes, returning the normalized result value.
        """
        raw_result = self._result.get(timeout=timeout, propagate=propagate)
        return self._deserialize_payload(raw_result)

    def _deserialize_payload(self, raw_result: Any) -> Any:
        """Helper to unpack job result containers."""
        if isinstance(raw_result, dict) and raw_result.get("__type__") == "dataclass":
            deserialized = deserialize(raw_result)
            if isinstance(deserialized, JobResult):
                return deserialized.value
        
        if isinstance(raw_result, JobResult):
            return raw_result.value
            
        return raw_result