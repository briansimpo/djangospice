from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from .options import WidgetOptions


class WidgetMetaclass(type):

    ACTION_COLLECTION_SUFFIX = "_actions"

    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        attrs: dict[str, Any],
    ) -> type:

        meta = attrs.get("Meta")
        module_path = attrs.get("__module__", "")

        cls = super().__new__(
            mcls,
            name,
            bases,
            attrs,
        )

        if not bases or bases == (object,):
            return cls

        cls._meta = WidgetOptions.from_meta(
            meta,
            name,
            module_path,
        )

        cls.actions = mcls.build_actions(
            bases,
            attrs.get("actions", ()),
        )

        mcls.build_named_action_collections(
            cls,
            bases,
            attrs,
        )

        return cls

    # ------------------------------------------------------------------
    # Canonical action collection
    # ------------------------------------------------------------------

    @staticmethod
    def build_actions(bases: tuple[type, ...], declared: Iterable[Any]):

        from djangospice.widgets.actions import ActionCollection

        action_map = {}

        for base in bases:

            inherited = getattr(
                base,
                "actions",
                (),
            )

            if isinstance(
                inherited,
                ActionCollection,
            ):
                inherited = tuple(inherited)

            for action in inherited:
                action_map[action.name] = deepcopy(action)

        for action in declared:
            action_map[action.name] = deepcopy(action)

        return ActionCollection(
            tuple(action_map.values())
        )

    # ------------------------------------------------------------------
    # Named action collections
    # ------------------------------------------------------------------

    @classmethod
    def build_named_action_collections(mcls, cls: type, bases: tuple[type, ...], attrs: dict[str, Any]) -> None:

        from djangospice.widgets.actions import ActionCollection

        names = set()

        # Discover declarations on this class.
        for name in attrs:
            if name.endswith(
                mcls.ACTION_COLLECTION_SUFFIX
            ):
                names.add(name)

        # Discover inherited declarations.
        for base in bases:
            for name in dir(base):
                if name.endswith(
                    mcls.ACTION_COLLECTION_SUFFIX
                ):
                    value = getattr(base, name, None)

                    if isinstance(
                        value,
                        ActionCollection,
                    ):
                        names.add(name)

        # Normalize every collection.
        for name in names:

            declared = attrs.get(name)

            if declared is None:

                # Preserve inherited collection.
                inherited = mcls.get_inherited_action_collection(bases,name)

                setattr(
                    cls,
                    name,
                    ActionCollection(
                        deepcopy(tuple(inherited))
                    ),
                )

                continue

            setattr(
                cls,
                name,
                mcls.normalize_action_collection(
                    declared
                ),
            )

    @staticmethod
    def normalize_action_collection(value: Any):

        from djangospice.widgets.actions import ActionCollection

        if isinstance(
            value,
            ActionCollection,
        ):
            return ActionCollection(
                deepcopy(tuple(value))
            )

        if value is None:
            return ActionCollection()

        return ActionCollection(
            deepcopy(tuple(value))
        )

    @staticmethod
    def get_inherited_action_collection(bases: tuple[type, ...], name: str):

        from djangospice.widgets.actions import ActionCollection

        for base in bases:

            value = getattr(
                base,
                name,
                None,
            )

            if isinstance(
                value,
                ActionCollection,
            ):
                return value

        return ActionCollection()