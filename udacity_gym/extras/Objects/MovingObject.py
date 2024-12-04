from .ObjectInterface import ObjectInterface



class MovingObject(ObjectInterface):
    def __init__(self, Name, Prefab ,Speed, SpawnPoint):
        self.Name = Name
        self.Speed = Speed
        self.SpawnPoint = SpawnPoint
        self.Prefab = Prefab

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
        return None
    def GetScaleVektor(self):
        return None


    def GetMessage(self):
        return {
            "command": self.GetCommand(),
                "name": self.GetName(),
                "speed": self.GetSpeed(),
                "spawn_point": self.GetSpawnPoint(),
                "prefab_name": self.GetPrefabName()
                }

