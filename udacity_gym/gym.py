import gymnasium as gym
import numpy as np
from gymnasium import spaces
from typing import Optional, Tuple, Any, SupportsFloat, List

from .action import UdacityAction
from .extras.Objects.ObjectInterface import ObjectInterface
from .logger import CustomLogger
from .observation import UdacityObservation
from .simulator import TrackName, WeatherName, DayTimeName


class UdacityGym(gym.Env):
    """
    Gym-Schnittstelle für den Udacity-Simulator
    """

    metadata = {
        "render.modes": ["human", "rgb_array"],
    }

    def __init__(
            self,
            simulator,
            max_steering: float = 1.0,
            max_throttle: float = 1.0,
            input_shape: Tuple[int, int, int] = (3, 160, 320),
    ):
        # Speichern von Objekteigenschaften und Parametern
        self.simulator = simulator

        self.max_steering = max_steering
        self.max_throttle = max_throttle
        self.input_shape = input_shape

        self.logger = CustomLogger(str(self.__class__))

        # Initialisierung der Gym-Umgebung
        # Lenkung + Gas, Aktionsraum muss symmetrisch sein
        self.action_space = spaces.Box(
            low=np.array([-max_steering, -max_throttle]),
            high=np.array([max_steering, max_throttle]),
            dtype=np.float32,
        )
        self.observation_space = spaces.Box(
            low=0, high=255, shape=input_shape, dtype=np.uint8
        )

        # Zähler für die maximale Schrittzahl pro Episode
        self.max_steps = 1000  # Beispielwert, kann angepasst werden
        self.current_step = 0

    def step(
            self,
            action: UdacityAction
    ) -> Tuple[UdacityObservation, SupportsFloat, bool, bool, dict[str, Any]]:
        """
        Führt einen Schritt in der Umgebung aus.

        :param action: (UdacityAction)
        :return: (UdacityObservation, float, bool, bool, dict)
        """
        # Ausführen der Aktion im Simulator
        observation = self.simulator.step(action)

        # Schrittzähler erhöhen
        self.current_step += 1

        # Festlegen der Bedingungen für 'done' und 'truncated'
        done = False
        truncated = False

        # Überprüfen auf bestimmte Ereignisse
        events = self.simulator.sim_state.get('events', [])

        # Wenn das Fahrzeug die Strecke verlassen hat
        if any(event['key'] == 'out_of_track' for event in events):
            done = True
            self.logger.info("Episode beendet: Fahrzeug hat die Strecke verlassen.")

        # Wenn das Fahrzeug kollidiert ist
        elif any(event['key'] == 'collision' for event in events):
            done = True
            self.logger.info("Episode beendet: Kollision erkannt.")

        # Wenn die maximale Schrittzahl erreicht wurde

        # Berechnen der Belohnung (Beispiel: negative absolute CTE)
        reward = -abs(observation.cte)

        # Zurücksetzen der Ereignisliste nach Verarbeitung
        self.simulator.sim_state['events'] = []

        return observation, reward, done, truncated, {
            'events': events,
            'episode_metrics': self.simulator.sim_state.get('episode_metrics', {}),
        }

    def reset(self, **kwargs) -> Tuple[UdacityObservation, dict[str, Any]]:
        """
        Setzt die Umgebung zurück und wartet synchron, bis die Strecke gesetzt wurde.

        :return: (UdacityObservation, dict)
        """
        track = kwargs.get('track', 'lake')
        weather = kwargs.get('weather', 'sunny')
        daytime = kwargs.get('daytime', 'day')

        # Konvertieren von Strings zu Enums, falls nötig
        try:
            track_enum = TrackName(track.lower())
        except ValueError:
            self.logger.error(f"Ungültiger Streckenname: {track}. Verwende Standardwert 'lake'.")
            track_enum = TrackName.LAKE

        try:
            weather_enum = WeatherName(weather.lower())
        except ValueError:
            self.logger.error(f"Ungültiger Wettername: {weather}. Verwende Standardwert 'sunny'.")
            weather_enum = WeatherName.SUNNY

        try:
            daytime_enum = DayTimeName(daytime.lower())
        except ValueError:
            self.logger.error(f"Ungültiger Tageszeitname: {daytime}. Verwende Standardwert 'day'.")
            daytime_enum = DayTimeName.DAY

        # Simulator zurücksetzen
        observation, info = self.simulator.reset(track_enum, weather_enum, daytime_enum)

        # Schrittzähler zurücksetzen
        self.current_step = 0

        return observation, info
    def render(self, mode: str = "human") -> Optional[np.ndarray]:
        if mode == "rgb_array":
            return self.simulator.sim_state['observation'].image_array
        return None

    def setothercars(self,
                     objects: List[ObjectInterface] = None):
        self.simulator.setothercars(objects)

    def observe(self) -> UdacityObservation:
        return self.simulator.observe()

    def close(self) -> None:
        if self.simulator is not None:
            self.simulator.close()
