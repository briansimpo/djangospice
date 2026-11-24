from __future__ import annotations

from typing import Any, ClassVar

from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.views import View

from .dispatchers import Dispatcher
from .identity import ClassIdentity
from .executable import Executable
from .resolver import Resolver



class ExecutableView(View):
    """
    Resolves, prepares, initializes, authorizes, and dispatches executables.
    """

    dispatchers: ClassVar[tuple[type[Dispatcher], ...]] = ()

    def get_executable(self, app_name: str, class_name: str) -> type[Executable]:
        identifier = ClassIdentity.build(
            app_name,
            class_name,
        ).to_string()

        return Resolver.resolve(identifier)

    def get_params(self, request: HttpRequest, **kwargs: Any) -> dict[str, Any]:
        return {
            **request.GET.dict(),
            **kwargs,
        }

    def create_instance(self, executable: type[Executable], request: HttpRequest, params: dict[str, Any]) -> Executable:
        instance = executable(**params)
        instance.set_request(request)
        return instance

    def prepare_instance(self, instance: Executable, request: HttpRequest, action: str | None = None, **kwargs: Any) -> None:
        """
        Hook for attaching additional context before initialization.
        """

    def initialize_instance(self, instance: Executable) -> None:
        instance.initialize()
        instance.configure()
        instance.authorize()

    def get_dispatchers(self, instance: Executable, request: HttpRequest, action: str | None) -> tuple[type[Dispatcher], ...]:
        return self.dispatchers

    def dispatch(self, request: HttpRequest, app_name: str, class_name: str, action: str | None = None, *args: Any, **kwargs: Any,) -> HttpResponse:

        try:
            executable = self.get_executable(
                app_name,
                class_name,
            )
        except LookupError as exc:
            raise Http404(str(exc)) from exc

        try:
            params = self.get_params(request, **kwargs)

            instance = self.create_instance(
                executable,
                request,
                params,
            )

            self.prepare_instance(
                instance,
                request,
                action=action,
                **kwargs,
            )

            self.initialize_instance(instance)

            for dispatcher_cls in self.get_dispatchers(instance, request, action):
                dispatcher = dispatcher_cls(
                    instance,
                    request,
                    action=action,
                )

                if dispatcher.can_dispatch():
                    return dispatcher.dispatch()

            raise LookupError(
                "No valid dispatcher found for this instance."
            )

        except PermissionDenied:
            raise Http404() from None
