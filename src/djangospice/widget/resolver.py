from __future__ import annotations

from typing import Any, TypeVar

from djangospice.core.object import ClassIdentity


from .registry import WidgetRegistry


WidgetT = TypeVar("WidgetT")


class WidgetResolver:
    """
    Resolves registered widgets from their application and name.

    The resolver is responsible only for discovery and validation. It does
    not instantiate, configure, or execute widgets.
    """

    @classmethod
    def resolve(cls, identifier, *, expected_type: type[WidgetT] | None = None) -> type[WidgetT]:
        """
        Resolve a registered widget class.

        ``expected_type`` can be supplied when a consumer requires a
        particular widget specialization, for example ``DynamicTable``.
        """
       
        try:
            widget_cls = WidgetRegistry.get(identifier)
        except KeyError:
            raise LookupError(
                f"Widget '{identifier}' is not registered."
            ) from None

        if widget_cls is None:
            raise LookupError(
                f"Widget '{identifier}' is not registered."
            )

        if expected_type is not None:
            if not issubclass(widget_cls, expected_type):
                raise TypeError(
                    f"Widget '{identifier}' must inherit from "
                    f"{expected_type.__name__}."
                )

        return widget_cls
