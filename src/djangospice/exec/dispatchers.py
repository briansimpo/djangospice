from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from django.http import HttpRequest, HttpResponseNotFound

from djangospice.exec.mixin import Executable
from djangospice.htmx.response import Response


ExecutableT = TypeVar("ExecutableT", bound=Executable)


class Dispatcher(ABC, Generic[ExecutableT]):
    """Abstract base class for executable dispatchers."""

    def __init__(self, executable: ExecutableT, request: HttpRequest, *, action: str | None = None) -> None:
        self.executable = executable
        self.request = request
        self.action = action

    @abstractmethod
    def can_dispatch(self) -> bool:
        pass

    @abstractmethod
    def dispatch(self) -> Response:
        pass


class MethodDispatcher(Dispatcher[Executable]):
    """Dispatches registered executable methods."""

    def can_dispatch(self) -> bool:
        return bool(
            self.action
            and self.action in self.executable.get_methods()
        )

    def dispatch(self) -> Response:
        method = self.executable.get_method(self.action)

        return method.execute(
            self.executable,
            self.request,
        )


class UnknownDispatcher(Dispatcher[Executable]):
    """Rejects unregistered widget actions."""

    def can_dispatch(self) -> bool:
        return self.action is not None

    def dispatch(self) -> Response:
        return HttpResponseNotFound(
            f"Widget action '{self.action}' not found."
        )

