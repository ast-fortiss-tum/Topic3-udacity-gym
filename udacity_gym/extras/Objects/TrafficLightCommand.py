from .TrafficLightInterface import TrafficLightInterface

class TrafficLightCommand(TrafficLightInterface):

    def __init__(self, Name, State):
        self.Name = Name
        self.State = State

    def GetName(self):
        return self.Name

    def GetCommand(self):
        return "control_traffic_Light"

    def GetState(self):
        return self.State

    def GetMessage(self):
        return {
            "command": self.GetCommand(),
            "trafficLightCommand": {
                "Name": self.GetName(),
                "State": self.GetState()
            }
        }