from .ObjectInterface import ObjectInterface



class MovingObject(ObjectInterface):
    def __init__(self, Name, Prefab, Speed, SpawnPoint, Offset, ScaleVektor, Rotation, Waypoints, Layer):
        self.Name = Name
        self.Prefab = Prefab
        self.Speed = Speed
        self.SpawnPoint = SpawnPoint
        self.Offset = Offset
        self.ScaleVektor = ScaleVektor
        self.Rotation = Rotation
        self.Waypoints = Waypoints
        self.Layer = Layer

    def GetCommand(self):
        return "spawn_car"

    def GetPrefabName(self):
        return "Objects/" + self.Prefab

    def GetName(self):
        return self.Name
    def GetSpeed(self):
        return self.Speed
    def GetScaleVektor(self):
        return self.ScaleVektor
    def GetSpawnPoint(self):
        return self.SpawnPoint
    def GetOffset(self):
        return self.Offset
    def GetRotation(self):
        return self.Rotation
    def GetWaitingPoints(self):
        return []
    def GetWaypoints(self):
        return  self.Waypoints
    def GetLayer(self):
        return self.Layer


    def GetMessage(self):
        return {
            "command": self.GetCommand(),
            "name": self.GetName(),
            "speed": self.GetSpeed(),
            "spawn_point": self.GetSpawnPoint(),
            "offset": self.GetOffset(),
            "scale_Vektor": self.GetScaleVektor(),
            "prefab_name": self.GetPrefabName(),
            "rotation": self.GetRotation(),
            "waitingPoints": self.GetWaitingPoints(),
            "waypoints": self.GetWaypoints(),
            "layer": self.GetLayer(),
        }

