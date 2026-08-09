import abc


class EventSubscriber(abc.ABC):
    """
    Groups multiple listeners under a single domain class.
    """
    @abc.abstractmethod
    def subscribe(self) -> None:
        """Registers listener bindings to the provided registry."""
        pass