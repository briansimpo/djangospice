from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class JobResult:
    """
    Guarantees a uniform return interface for every background job execution.
    """
    value: Any