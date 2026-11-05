import importlib
import inspect
import pkgutil

from django.apps import apps
from django.template.backends.django import DjangoTemplates
from django.template.library import import_library
from djangospice.package.helpers import is_djangospice_app


def discover_template_libraries():
    """
    Discover template tag libraries from installed Djangospice apps.

    Convention:
        app/
            templatetags/
                __init__.py
                widgets.py
                components.py
    """
    for app_config in apps.get_app_configs():
        if not is_djangospice_app(app_config):
            continue

        package_name = f"{app_config.name}.templatetags"

        try:
            package = importlib.import_module(package_name)
        except ModuleNotFoundError as exc:
            if exc.name == package_name:
                continue
            raise

        if not hasattr(package, "__path__"):
            continue

        for module in pkgutil.iter_modules(
            package.__path__,
            prefix=f"{package_name}.",
        ):
            if module.ispkg or module.name.rsplit(".", 1)[-1].startswith("_"):
                continue

            yield module.name


def discover_context_processors():
    """
    Discover public context processor functions.

    Convention:
        app/
            context_processors.py

    Every public function defined in context_processors.py is
    considered a context processor.

    Alternatively, define __all__ to explicitly select functions.
    """
    for app_config in apps.get_app_configs():
        if not is_djangospice_app(app_config):
            continue

        module_name = f"{app_config.name}.context_processors"

        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                continue
            raise

        exported = getattr(module, "__all__", None)

        if exported is None:
            names = (
                name
                for name, value in vars(module).items()
                if not name.startswith("_")
                and inspect.isfunction(value)
                and value.__module__ == module.__name__
            )
        else:
            names = iter(exported)

        for name in names:
            processor = getattr(module, name)

            if (
                not inspect.isfunction(processor)
                or processor.__module__ != module.__name__
            ):
                raise TypeError(
                    f"{module_name}.{name} must be a function "
                    "defined in the context_processors module."
                )

            yield f"{module_name}.{name}"


def register_template_libraries(engine):
    """
    Register discovered template tag libraries as template builtins.
    """
    registered = getattr(
        engine,
        "_djangospice_registered_template_libraries",
        None,
    )

    if registered is None:
        registered = set()
        engine._djangospice_registered_template_libraries = registered

    for library_name in discover_template_libraries():
        if library_name in registered:
            continue

        library = import_library(library_name)

        engine.template_builtins.append(library)
        registered.add(library_name)


def register_context_processors(engine):
    """
    Register discovered context processors on the Django template engine.
    """
    registered = getattr(
        engine,
        "_djangospice_registered_context_processors",
        None,
    )

    if registered is None:
        registered = set()
        engine._djangospice_registered_context_processors = registered

    for processor_path in discover_context_processors():
        if processor_path in registered:
            continue

        if processor_path not in engine.context_processors:
            engine.context_processors.append(processor_path)

        registered.add(processor_path)

    # Django caches the imported context processor functions.
    # Invalidate that cache in case registration happens after access.
    engine.__dict__.pop("template_context_processors", None)


def register_template_tags():
    """
    Register all Djangospice template libraries and context processors
    in every configured Django template backend.
    """
    for backend in __import__(
        "django.template",
        fromlist=["engines"],
    ).engines.all():

        if not isinstance(backend, DjangoTemplates):
            continue

        engine = backend.engine

        register_template_libraries(engine)
        register_context_processors(engine)
