from contextvars import ContextVar
from .reporter import JobReporter

active_reporter: ContextVar[JobReporter | None] = ContextVar(
    "active_reporter",
    default=None,
)
