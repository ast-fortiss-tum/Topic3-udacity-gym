from .ObjectInterface import ObjectInterface

class GenerateTrack(ObjectInterface):
    def __init__(self, trackdata, RandomCarAmount):
        self.trackdata = trackdata  # Komma entfernt!
        self.RandomCarAmount = RandomCarAmount

    def GetCommand(self):
        return "Generate_Track"

    def GetTrackDataList(self):
        return self.trackdata

    def GetMessage(self):
        return {
            "command": self.GetCommand(),
            "trackDataList": self.GetTrackDataList(),
            "randomCarAmount": self.GetRandomCarAmount()
        }

    def GetRandomCarAmount(self):
        return self.RandomCarAmount

    # Implementierung der abstrakten Methoden aus ObjectInterface:

    def GetName(self):
        return "GenerateTrack"

    def GetSpeed(self):
        return 0  # Beispielwert, falls Geschwindigkeit nicht benötigt wird

    def GetOffset(self):
        return [0, 0, 0]  # Beispieloffset

    def GetScaleVektor(self):
        return [1, 1, 1]  # Standardmaßstab

    def GetSpawnPoint(self):
        return [0, 0, 0]  # Beispiel-Spawnpunkt

    def GetPrefabName(self):
        return ""  # Kein Prefabname

    def GetRotation(self):
        return [0, 0, 0]  # Standardrotation

    def GetWaitingPoints(self):
        return []  # Keine Wartepunkte

    def GetWaypoints(self):
        return []  # Keine Waypoints

    def GetLayer(self):
        return 0  # Standardlayer

    def GetHumanBehavior(self):
        return None  # Keine spezielle HumanBehavior
