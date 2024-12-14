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

    @abstractmethod
    def GetPrefabName(self):
        pass

    @abstractmethod
    def GetRotation(self):
        pass

    @abstractmethod
    def GetWaitingPoints(self):
        pass

    @abstractmethod
    def GetWaypoints(self):
        pass

    @abstractmethod
    def GetLayer(self):
        pass

    @abstractmethod
    def GetHumanBehavior(self):
        pass