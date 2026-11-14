from typing import Any, Callable

from djangospice.exec.decorators import get, post


def _group_action(
    decorator,
    group: str,
    func: Callable | None = None,
    **attributes: Any,
):
    attributes["group"] = group

    wrapped = decorator(**attributes)

    return wrapped(func) if func is not None else wrapped


def table_action(func=None, **attributes: Any):
    """Declare a table-level action."""
    return _group_action(get, "table", func, **attributes)


def row_action(func=None, **attributes: Any):
    """Declare a row-level action."""
    return _group_action(get, "row", func, **attributes)


def bulk_action(func=None, **attributes: Any):
    """Declare a bulk action."""
    return _group_action(post, "bulk", func, **attributes)