from contextvars import ContextVar
from typing import Any

active_reporter: ContextVar[Any | None] = ContextVar(
    "active_reporter",
    default=None,
)
