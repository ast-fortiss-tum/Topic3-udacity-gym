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


    def GetMessage(self):
        return {
            "command": object.GetCommand(),
                "name": object.GetName(),
                "spawn_point": object.GetSpawnPoint(),
                "offset": object.GetOffset(),
                "scale_Vektor": object.GetScaleVektor()
                }