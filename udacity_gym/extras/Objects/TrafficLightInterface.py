
from abc import ABC, abstractmethod

class TrafficLightInterface(ABC):

    @abstractmethod
    def GetCommand(self):
        pass

    @abstractmethod
    def GetName(self):
        pass

    @abstractmethod
    def GetState(self):
        pass

    @abstractmethod
    def GetPhaseDelay(self):
        pass

    @abstractmethod
    def GetMessage(self):
        pass