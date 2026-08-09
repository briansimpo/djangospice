from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator, Sequence
from functools import cached_property

from .action import Action


class ActionCollection(Sequence[Action]):
    """
    Immutable collection of widget actions.

    Provides fast lookup by name and efficient grouping for rendering.
    """

    def __init__(self, actions: Sequence[Action] = ()) -> None:
        self._actions = tuple(actions)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    @cached_property
    def _map(self) -> dict[str, Action]:
        return {
            action.name: action
            for action in self._actions
        }

    @cached_property
    def _groups(self) -> dict[str, tuple[Action, ...]]:
        groups: dict[str, list[Action]] = defaultdict(list)

        for action in self._actions:
            for group in action.groups:
                groups[group].append(action)

        return {
            name: tuple(sorted(actions, key=lambda a: a.order))
            for name, actions in groups.items()
        }

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------

    def get(self, name: str) -> Action | None:
        """
        Return an action by name.
        """
        return self._map.get(name)

    def require(self, name: str) -> Action:
        """
        Return an action or raise KeyError.
        """
        try:
            return self._map[name]
        except KeyError:
            raise KeyError(f"Unknown action '{name}'") from None

    # ------------------------------------------------------------------
    # Sequence
    # ------------------------------------------------------------------

    def __getitem__(self, index):
        return self._actions[index]

    def __iter__(self) -> Iterator[Action]:
        return iter(self._actions)

    def __len__(self) -> int:
        return len(self._actions)

    def __contains__(self, item: object) -> bool:
        return item in self._actions

    def __bool__(self) -> bool:
        return bool(self._actions)