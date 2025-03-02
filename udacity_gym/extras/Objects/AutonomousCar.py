from .ObjectInterface import ObjectInterface



class AutonomousCar(ObjectInterface):
    def __init__(self, Waypoints):
        self.Waypoints = Waypoints


    def GetCommand(self):
        return "spawn_autonomous_car"

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
    def GetHumanBehavior(self):
        return self.HumanBehavior

    def GetMessage(self):
        return {
            "command": self.GetCommand(),
            "waypoints": self.GetWaypoints(),
        }

