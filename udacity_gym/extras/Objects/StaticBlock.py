from .ObjectInterface import ObjectInterface

class StaticBlock(ObjectInterface):

    def __init__(self, Name, Prefab ,SpawnPoint, Offset, ScaleVektor, Rotation):
        self.Name = Name
        self.Prefab = Prefab
        self.SpawnPoint = SpawnPoint
        self.Offset = Offset
        self.ScaleVektor = ScaleVektor
        self.Rotation = Rotation


    def GetPrefabName(self):
        return "Objects/" + self.Prefab

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

    def GetRotation(self):
        return self.Rotation

    def GetHumanBehavior(self):
        return None

    def GetMessage(self):
        return {
            "command": self.GetCommand(),
                "name": self.GetName(),
                "spawn_point": self.GetSpawnPoint(),
                "offset": self.GetOffset(),
                "scale_Vektor": self.GetScaleVektor(),
                "prefab_name": self.GetPrefabName(),
                "rotation": self.GetRotation()
                }