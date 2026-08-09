from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Iterable

if TYPE_CHECKING:
    from djangospice.widgets.actions import ActionCollection

from .options import WidgetOptions


class WidgetMetaclass(type):
    """
    Metaclass for widgets.

    Responsibilities
    ----------------
    - Build WidgetOptions from the inner Meta class.
    - Normalize declarative widget definitions.
    - Merge inherited declarations.
    """

    def __new__(mcls, name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> type:

        meta = attrs.get("Meta")
        module_path = attrs.get("__module__", "")

        cls = super().__new__(mcls, name, bases, attrs)

        # Don't process the root widget class.
        if not bases or bases == (object,):
            return cls

        # ------------------------------------------------------------------
        # Widget metadata
        # ------------------------------------------------------------------

        cls._meta = WidgetOptions.from_meta(
            meta,
            name,
            module_path,
        )

        # ------------------------------------------------------------------
        # Normalize declarative attributes
        # ------------------------------------------------------------------

        cls.actions = mcls.build_actions(
            bases,
            attrs.get("actions", ()),
        )

        return cls

    # ----------------------------------------------------------------------
    # Builders
    # ----------------------------------------------------------------------

    @staticmethod
    def build_actions(bases: tuple[type, ...], declared: Iterable[Any]) -> ActionCollection:
        """
        Merge inherited and declared actions.

        ActionCollection are identified by their unique ``name``.
        Child widgets replace parent actions with the same name.
        """
        from djangospice.widgets.actions import ActionCollection

        action_map = {}


        for base in bases:
            actions = getattr(base, "actions", ())

            if isinstance(actions, ActionCollection):
                actions = tuple(actions)

            for action in actions:
                action_map[action.name] = deepcopy(action)

        #
        # declared
        #
        for action in declared:
            action_map[action.name] = deepcopy(action)

        return ActionCollection(tuple(action_map.values()))