from abc import ABC
from abc import abstractmethod


class Startable(ABC):

    @abstractmethod
    def start(self):
        pass


class Stoppable(ABC):

    @abstractmethod
    def stop(self):
        pass