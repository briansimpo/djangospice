from dataclasses import dataclass
from ..widgets.interaction import Interaction


@dataclass(frozen=True, slots=True)
class Pagination:
    number: int
    total: int

    has_previous: bool
    has_next: bool

    previous: Interaction | None
    next: Interaction | None

    first: Interaction | None
    last: Interaction | None

    pages: tuple[
        tuple[int, Interaction, bool],
        ...
    ]