from .TrafficLightInterface import TrafficLightInterface

class ControlTrafficManager(TrafficLightInterface):

    def __init__(self, Name, State, PhaseDelay):
        self.Name = Name
        self.State = State
        self.PhaseDelay = PhaseDelay

    def GetName(self):
        return self.Name

    def GetCommand(self):
        return "control_traffic_Manager"

    def GetState(self):
        return self.State

    def GetPhaseDelay(self):
        return self.PhaseDelay

    def GetMessage(self):
        return {
            "command": self.GetCommand(),
            "trafficLightManager": {
                "ManagerName": self.GetName(),
                "PhaseList": self.GetState(),
                "PhaseDelay": self.GetPhaseDelay()
            }
        }