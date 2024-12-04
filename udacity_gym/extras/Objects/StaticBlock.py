from .ObjectInterface import ObjectInterface

class StaticBlock(ObjectInterface):
    def __init__(self, Name, SpawnPoint, Offset, ScaleVektor):
        self.Name = Name
        self.SpawnPoint = SpawnPoint
        self.Offset = Offset
        self.ScaleVektor = ScaleVektor

    def GetCommand(self):
        return "spawn_static_object"

    def GetName(self):
        return self.Name

    def GetSpeed(self):
        return None

    def GetScaleVektor(self):
        return self.ScaleVektor

    def GetSpawnPoint(self):
        return self.SpawnPoint

    def GetOffset(self):
        return self.Offset

    def GetPrefabName(self):
        return "Objects/House"


    def GetMessage(self):
        return {
            "command": self.GetCommand(),
                "name": self.GetName(),
                "spawn_point": self.GetSpawnPoint(),
                "offset": self.GetOffset(),
                "scale_Vektor": self.GetScaleVektor(),
                "prefab_name": self.GetPrefabName()
                }