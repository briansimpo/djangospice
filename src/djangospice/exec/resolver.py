from .registry import Registry
from .mixin import Executable


class Resolver:
    """
    Resolves registered widgets from their application and name.

    The resolver is responsible only for discovery and validation. It does
    not instantiate, configure, or execute widgets.
    """

    @classmethod
    def resolve(cls, identifier, *, expected_type: type[Executable] | None = None) -> type[Executable]:
        """
        Resolve a registered widget class.

        ``expected_type`` can be supplied when a consumer requires a
        particular widget specialization, for example ``DynamicTable``.
        """
       
        try:
            exec_klass = Registry.get(identifier)
        except KeyError:
            raise LookupError(
                f"Executable '{identifier}' is not registered."
            ) from None

        if exec_klass is None:
            raise LookupError(
                f"Executable '{identifier}' is not registered."
            )

        if expected_type is not None:
            if not issubclass(exec_klass, expected_type):
                raise TypeError(
                    f"Executable '{identifier}' must inherit from "
                    f"{expected_type.__name__}."
                )

        return exec_klass