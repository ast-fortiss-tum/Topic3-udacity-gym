from .ObjectInterface import ObjectInterface



class MovingObject(ObjectInterface):
    def __init__(self, Name, Prefab, Speed, Offset, SpawnPoint, ScaleVektor, Rotation):
        self.Name = Name
        self.Speed = Speed
        self.Offset = Offset
        self.SpawnPoint = SpawnPoint
        self.Prefab = Prefab
        self.ScaleVektor = ScaleVektor
        self.Rotation = Rotation

    def GetCommand(self):
        return "spawn_car"

    def GetPrefabName(self):
        return "Objects/" + self.Prefab

    def GetName(self):
        return self.Name
    def GetSpeed(self):
        return self.Speed
    def GetSpawnPoint(self):
        return self.SpawnPoint
    def GetOffset(self):
        return self.Offset
    def GetScaleVektor(self):
        return self.ScaleVektor

    def GetRotation(self):
        return self.Rotation


    def GetMessage(self):
        return {
            "command": self.GetCommand(),
            "name": self.GetName(),
            "speed": self.GetSpeed(),
            "offset": self.GetOffset(),
            "spawn_point": self.GetSpawnPoint(),
            "prefab_name": self.GetPrefabName(),
            "scale_Vektor": self.GetScaleVektor(),
            "rotation": self.GetRotation()
            }

