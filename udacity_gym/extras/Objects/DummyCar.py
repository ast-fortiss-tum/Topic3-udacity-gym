from .ObjectInterface import ObjectInterface



class DummyCar(ObjectInterface):
    def __init__(self, Name, Speed, SpawnPoint):
        self.Name = Name
        self.Speed = Speed
        self.SpawnPoint = SpawnPoint

    def GetCommand(self):
        return "spawn_car"

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
            "command": object.GetCommand(),
                "name": object.GetName(),
                "speed": object.GetSpeed(),
                "spawn_point": object.GetSpawnPoint(),
                }

