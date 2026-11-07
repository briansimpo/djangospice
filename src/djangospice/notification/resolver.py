from .registry import NotificationRegistry
from .base import Notification


class NotificationResolver:
    """
    Resolves registered widgets from their application and name.

    The resolver is responsible only for discovery and validation. It does
    not instantiate, configure, or execute widgets.
    """

    @classmethod
    def resolve(cls, identifier, *, expected_type: type[Notification] | None = None) -> type[Notification]:
        """
        Resolve a registered widget class.

        ``expected_type`` can be supplied when a consumer requires a
        particular widget specialization, for example ``DynamicTable``.
        """
       
        try:
            widget_klass = NotificationRegistry.get(identifier)
        except KeyError:
            raise LookupError(
                f"Notification '{identifier}' is not registered."
            ) from None

        if widget_klass is None:
            raise LookupError(
                f"Notification '{identifier}' is not registered."
            )

        if expected_type is not None:
            if not issubclass(widget_klass, expected_type):
                raise TypeError(
                    f"Notification '{identifier}' must inherit from "
                    f"{expected_type.__name__}."
                )

        return widget_klass