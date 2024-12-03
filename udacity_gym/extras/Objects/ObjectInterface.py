from abc import ABC, abstractmethod

class ObjectInterface(ABC):

    @abstractmethod
    def GetCommand(self):
        pass

    @abstractmethod
    def GetName(self):
        pass

    @abstractmethod
    def GetSpeed(self):
        pass

    @abstractmethod
    def GetOffset(self):
        pass

    @abstractmethod
    def GetScaleVektor(self):
        pass

    @abstractmethod
    def GetMessage(self):
        pass

    @abstractmethod
    def GetSpawnPoint(self):
        pass
