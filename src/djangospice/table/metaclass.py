from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from djangospice.widgets.actions import Action, ActionCollection
from djangospice.widgets.metaclass import WidgetMetaclass


class TableWidgetMetaclass(WidgetMetaclass):
    """
    Metaclass for TableWidget.

    Normalizes the semantic action collections used by a table:

        table_actions
        row_actions
        bulk_actions

    Each collection is inherited and merged by action name.

    The three collections remain the developer-facing API while
    ``actions`` becomes the canonical registry used by ActionDispatcher.
    """

    action_collections = (
        "table_actions",
        "row_actions",
        "bulk_actions",
    )

    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        attrs: dict[str, Any],
    ) -> type:

        cls = super().__new__(
            mcls,
            name,
            bases,
            attrs,
        )

        # The base TableWidget itself does not need normalization.
        if name == "TableWidget":
            return cls

        # --------------------------------------------------------------
        # Normalize semantic collections
        # --------------------------------------------------------------

        for collection_name in mcls.action_collections:
            collection = mcls.build_collection(
                bases=bases,
                declared=attrs.get(collection_name, ()),
                collection_name=collection_name,
            )

            setattr(cls, collection_name, collection)

        # --------------------------------------------------------------
        # Build canonical action registry
        # --------------------------------------------------------------

        cls.actions = mcls.build_canonical_actions(
            cls=cls,
            bases=bases,
        )

        return cls

    # ------------------------------------------------------------------
    # Collection builder
    # ------------------------------------------------------------------

    @staticmethod
    def build_collection(
        *,
        bases: tuple[type, ...],
        declared: Iterable[Action],
        collection_name: str,
    ) -> ActionCollection:
        """
        Build one semantic action collection.

        Inherited actions are preserved.

        A child action with the same name replaces the inherited action.
        """

        action_map: dict[str, Action] = {}

        # --------------------------------------------------------------
        # Inherited actions
        # --------------------------------------------------------------

        for base in bases:
            inherited = getattr(
                base,
                collection_name,
                (),
            )

            if isinstance(inherited, ActionCollection):
                inherited = tuple(inherited)

            for action in inherited:
                action_map[action.name] = deepcopy(action)

        # --------------------------------------------------------------
        # Declared actions
        # --------------------------------------------------------------

        for action in declared:
            if not isinstance(action, Action):
                raise TypeError(
                    f"{collection_name} may only contain Action "
                    f"instances; got {type(action).__name__}."
                )

            action_map[action.name] = deepcopy(action)

        # --------------------------------------------------------------
        # Deterministic ordering
        # --------------------------------------------------------------

        return ActionCollection(
            tuple(
                sorted(
                    action_map.values(),
                    key=lambda action: (
                        action.order,
                        action.name,
                    ),
                )
            )
        )

    # ------------------------------------------------------------------
    # Canonical registry
    # ------------------------------------------------------------------

    @classmethod
    def build_canonical_actions(
        mcls,
        *,
        cls: type,
        bases: tuple[type, ...],
    ) -> ActionCollection:
        """
        Build the canonical action registry.

        ``Widget.actions`` is intentionally kept generic. TableWidget
        contributes its semantic action collections to that registry.
        """

        action_map: dict[str, Action] = {}

        # --------------------------------------------------------------
        # Generic inherited actions
        # --------------------------------------------------------------

        for base in bases:
            inherited = getattr(base, "actions", ())

            if isinstance(inherited, ActionCollection):
                inherited = tuple(inherited)

            for action in inherited:
                action_map[action.name] = deepcopy(action)

        # --------------------------------------------------------------
        # Table semantic collections
        # --------------------------------------------------------------

        for collection_name in mcls.action_collections:
            collection = getattr(
                cls,
                collection_name,
                (),
            )

            if isinstance(collection, ActionCollection):
                collection = tuple(collection)

            for action in collection:
                action_map[action.name] = deepcopy(action)

        return ActionCollection(
            tuple(
                sorted(
                    action_map.values(),
                    key=lambda action: (
                        action.order,
                        action.name,
                    ),
                )
            )
        )