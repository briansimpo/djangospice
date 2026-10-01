from __future__ import annotations

from importlib import import_module
from types import ModuleType

from django.apps import apps
from rest_framework.routers import BaseRouter


DEFAULT_ROUTER_MODULE = "api.router"
DEFAULT_ROUTER_ATTRIBUTE = "router"


def discover_routers(
    *,
    module_path: str = DEFAULT_ROUTER_MODULE,
    attribute: str = DEFAULT_ROUTER_ATTRIBUTE,
) -> list[BaseRouter]:
    """
    Discover API routers exposed by installed Django applications.

    By convention, applications expose their router at:

        <app>.api.router

    and the module exposes a DRF router named:

        router

    Applications without the specified router module or attribute are
    ignored.

    ModuleNotFoundError exceptions raised by dependencies inside an
    existing router module are propagated.
    """
    routers: list[BaseRouter] = []

    for app_config in apps.get_app_configs():
        module_name = f"{app_config.name}.{module_path}"

        module = _import_optional_module(module_name)

        if module is None:
            continue

        app_router = getattr(module, attribute, None)

        if app_router is None:
            continue

        if not isinstance(app_router, BaseRouter):
            raise TypeError(
                f"{module_name}.{attribute} must be an instance of "
                f"rest_framework.routers.BaseRouter; "
                f"got {type(app_router).__name__!r}."
            )

        routers.append(app_router)

    return routers


def _import_optional_module(module_name: str) -> ModuleType | None:
    """
    Import an optional module.

    Only a missing target module is ignored. Missing dependencies or
    import errors originating from the target module are propagated.
    """
    try:
        return import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            return None