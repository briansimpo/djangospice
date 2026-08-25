from typing import Any
from djangospice.core.serializer import serialize, deserialize


class SerializesModels:
    """
    Mixin applied directly to database models. Intercepts Pickling transitions
    to swap model hierarchies with clean, performant references.
    """
    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        return {k: serialize(v) for k, v in state.items()}

    def __setstate__(self, state: dict[str, Any]) -> None:
        deserialized_state = {k: deserialize(v) for k, v in state.items()}
        self.__dict__.update(deserialized_state)