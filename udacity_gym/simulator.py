import copy
import pathlib
import time
from enum import Enum
from typing import List, Union

from sympy import true

from .global_manager import get_simulator_state
from .action import UdacityAction
from .logger import CustomLogger
from .observation import UdacityObservation
from .unity_process import UnityProcess
from .Executor2 import UdacityExecutor  # Stellen Sie sicher, dass dies korrekt importiert wird

# Konstanten für den Simulatorzustand und Schlafdauer
SLEEP_DURATION = 0.1
SIM_STATE_PAUSED = 'paused'
SIM_STATE_RUNNING = 'running'


# Enums für Track, Wetter und Tageszeit
class TrackName(Enum):
    LAKE = 'lake'
    JUNGLE = 'jungle'
    MOUNTAIN = 'mountain'
    ROAD_GENERATOR = 'road_generator'


class WeatherName(Enum):
    SUNNY = 'sunny'
    RAINY = 'rainy'
    FOGGY = 'foggy'
    SNOWY = 'snowy'


class DayTimeName(Enum):
    DAY = 'day'
    DAYNIGHT = 'daynight'


# Abstrakte Simulator-Klasse (kann angepasst werden)
class AbstractSimulator:
    def step(self, action):
        pass

    def observe(self):
        pass

    def pause(self, sync=True):
        pass

    def resume(self, sync=True):
        pass

    def reset(self):
        pass

    def start(self):
        pass

    def close(self):
        pass


class UdacitySimulator(AbstractSimulator):

    def __init__(
            self,
            sim_exe_path: str = "./examples/udacity/udacity_utils/sim/udacity_sim.app",
            host: str = "127.0.0.1",
            command_port: int = 55002,
            telemetry_port: int = 56002,
            events_port: int = 57002,
            other_cars_port: int = 58002
    ):
        # Simulatorpfad
        self.simulator_exe_path = sim_exe_path
        self.sim_process = UnityProcess()
        # Netzwerkeinstellungen für den Simulator
        self.sim_executor = UdacityExecutor(host, command_port, telemetry_port, events_port, other_cars_port)
        self.host = host
        self.command_port = command_port
        self.telemetry_port = telemetry_port
        self.events_port = events_port
        self.other_cars_port = other_cars_port
        # Logging für den Simulator
        self.logger = CustomLogger(str(self.__class__))
        # Zustand des Simulators
        self.sim_state = get_simulator_state()

        # Überprüfen, ob die Binärdatei existiert
        if not pathlib.Path(sim_exe_path).exists():
            self.logger.error(f"Executable binary to the simulator does not exist. "
                              f"Check if the path {self.simulator_exe_path} is correct.")

    def step(self, action: UdacityAction):
        self.sim_state['action'] = action
        return self.observe()

    def observe(self):
        return self.sim_state['observation']

    def pause(self, sync=True):
        # Sende Pause-Befehl über EventPort
        self.sim_executor.send_pause()
        if sync:
            # Warte auf Bestätigung vom Simulator
            while self.sim_state.get('sim_state', '') != SIM_STATE_PAUSED:
                time.sleep(SLEEP_DURATION)

    def resume(self, sync=True):
        # Sende Resume-Befehl über EventPort
        self.sim_executor.send_resume()
        if sync:
            # Warte auf Bestätigung vom Simulator
            while self.sim_state.get('sim_state', '') != SIM_STATE_RUNNING:
                time.sleep(SLEEP_DURATION)

    def reset(
            self,
            new_track_name: Union[TrackName, str] = TrackName.LAKE,
            new_weather_name: Union[WeatherName, str] = WeatherName.SUNNY,
            new_daytime_name: Union[DayTimeName, str] = DayTimeName.DAY,
    ):
        # Konvertieren von Strings zu Enums, falls nötig
        if isinstance(new_track_name, str):
            try:
                new_track_name = TrackName(new_track_name.lower())
            except ValueError:
                self.logger.error(f"Ungültiger Streckenname: {new_track_name}. Verwende Standardwert 'lake'.")
                new_track_name = TrackName.LAKE

        if isinstance(new_weather_name, str):
            try:
                new_weather_name = WeatherName(new_weather_name.lower())
            except ValueError:
                self.logger.error(f"Ungültiger Wettername: {new_weather_name}. Verwende Standardwert 'sunny'.")
                new_weather_name = WeatherName.SUNNY

        if isinstance(new_daytime_name, str):
            try:
                new_daytime_name = DayTimeName(new_daytime_name.lower())
            except ValueError:
                self.logger.error(f"Ungültiger Tageszeitname: {new_daytime_name}. Verwende Standardwert 'day'.")
                new_daytime_name = DayTimeName.DAY

        # Setze Beobachtungen und Aktionen zurück
        observation = UdacityObservation(
            input_image=None,
            semantic_segmentation=None,
            position=(0.0, 0.0, 0.0),
            steering_angle=0.0,
            throttle=0.0,
            speed=0.0,
            cte=0.0,
            lap=0,
            sector=0,
            next_cte=0.0,
            time=-1
        )
        action = UdacityAction(
            steering_angle=0.0,
            throttle=0.0,
        )
        self.sim_state['observation'] = observation
        self.sim_state['action'] = action
        self.sim_state['events'] = []
        self.sim_state['episode_metrics'] = None
        self.sim_state['track_set'] = False  # Fügen Sie dies hinzu, um den Status zu verfolgen

        # Sende Reset-Befehl über EventPort mit Enums
        self.sim_executor.send_track(
            new_track_name.value,
            new_weather_name.value,
            new_daytime_name.value,
        )

        # Warten, bis der Simulator bestätigt, dass die Strecke gesetzt wurde
        while not self.sim_state.get('track_set', False):
            self.logger.info("Warte darauf, dass der Simulator die Strecke setzt...")
            time.sleep(0.1)

        # Nachdem die Strecke gesetzt wurde, setzen wir 'track_set' zurück
        self.sim_state['track_set'] = False

        return observation, {}

    def setothercars(self,
                     speedPerCar: List[int] = None,
                    start_positions: List[int] = None):
        self.sim_executor.send_spawn_cars(speedPerCar, start_positions)

    def start(self):
        # Starte Unity-Simulationsprozess
        self.logger.info("Starting Unity process for Udacity simulator...")
        self.sim_process.start(
            sim_path=self.simulator_exe_path,
            headless=False,
            command_port=self.command_port,
            telemetry_port=self.telemetry_port,
            events_port=self.events_port,
            other_cars_port=self.other_cars_port
        )
        self.sim_executor.start()

    def close(self):
        self.sim_process.close()
