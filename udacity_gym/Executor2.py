import base64
import io
import json
import socket
import threading
import time
from typing import List

from PIL import Image
from enum import Enum

from udacity_gym.extras.Objects import TrafficLightInterface, ControlTrafficManager
from udacity_gym.extras.Objects.MovingObject import MovingObject
from udacity_gym.extras.Objects.ObjectInterface import ObjectInterface
from udacity_gym.extras.Objects.StaticBlock import StaticBlock
from udacity_gym.extras.Objects.TrafficLightCommand import TrafficLightCommand
from udacity_gym.extras.Objects.ControlTrafficManager import ControlTrafficManager
from udacity_gym.global_manager import get_simulator_state
from udacity_gym.logger import CustomLogger
from udacity_gym.observation import UdacityObservation


class SimStates(Enum):
    RUNNING = 'running'
    STOPPED = 'stopped'
    PAUSED = 'paused'
    RESUMED = 'resumed'


class UdacityExecutor:
    def __init__(
            self,
            host: str = '127.0.0.1',
            command_port: int = 55001,
            telemetry_port: int = 56001,
            events_port: int = 57001,
            car_spawner_port: int = 58001,
    ):
        """Initializes the executor with host and ports for command and telemetry connections."""
        self.host = host
        self.command_port = command_port
        self.telemetry_port = telemetry_port
        self.events_port = events_port
        self.car_spawner_port = car_spawner_port
        self.command_sock = None
        self.telemetry_sock = None
        self.events_sock = None
        self.spawner_sock = None
        self.running = False
        self.sim_state = get_simulator_state()
        self.logger = CustomLogger(str(self.__class__))
        self.buffer = ''
        self.telemetry_lock = threading.Lock()
        self.logger.info("UdacityExecutor initialized.")

    def connect_to_server(self):
        """Attempts to establish connections to the servers."""
        self.logger.info("Attempting to connect to the server.")
        timeout = 60
        start_time = time.time()
        while time.time() - start_time < timeout:
            all_connected = True
            try:
                if not self.command_sock:
                    self.command_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.command_sock.connect((self.host, self.command_port))
                    self.logger.info(f"Connected to the command server at {self.host}:{self.command_port}.")
            except Exception as e:
                self.logger.error(f"Error connecting to the command server on port {self.command_port}: {e}")
                self.command_sock = None
                all_connected = False

            try:
                if not self.telemetry_sock:
                    self.telemetry_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.telemetry_sock.connect((self.host, self.telemetry_port))
                    self.logger.info(f"Connected to the telemetry server at {self.host}:{self.telemetry_port}.")
            except Exception as e:
                self.logger.error(f"Error connecting to the telemetry server on port {self.telemetry_port}: {e}")
                self.telemetry_sock = None
                all_connected = False

            try:
                if not self.events_sock:
                    self.events_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.events_sock.connect((self.host, self.events_port))
                    self.logger.info(f"Connected to the event server at {self.host}:{self.events_port}.")
            except Exception as e:
                self.logger.error(f"Error connecting to the event server on port {self.events_port}: {e}")
                self.events_sock = None
                all_connected = False

            try:
                if not self.spawner_sock:
                    self.spawner_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.spawner_sock.connect((self.host, self.car_spawner_port))
                    self.logger.info(f"Connected to CarSpawner server at {self.host}:{self.car_spawner_port}.")
            except Exception as e:
                self.logger.error(f"Error connecting to the CarSpawner server on port {self.car_spawner_port}: {e}")
                self.spawner_sock = None
                all_connected = False

            if all_connected:
                self.logger.info("Successfully connected to all servers.")
                break
            else:
                self.logger.warning("Failed to connect to all servers. Retrying in 2 seconds...")
                time.sleep(2)
        else:
            self.logger.error("Failed to connect to servers within timeout period.")
            self.close()

    def send_control(self):
        """Sends control commands to the simulator."""

        action = self.sim_state.get('action', None)
        if action:
            control_data = {
                "command": "send_control",
                "steering_angle": action.steering_angle,
                "throttle": action.throttle,
            }
            self.logger.debug(f"Prepared control data: {control_data}")
            self.send_message(control_data, self.command_sock)

    def send_message(self, message, currentSocket):
        """Sends a message to the specified socket."""
        self.logger.debug(f"Attempting to send message: {message}")
        if currentSocket:
            try:
                data = json.dumps(message).encode('utf-8') + b'\n'
                currentSocket.sendall(data)
                self.logger.info(f"Message sent: {message}")
            except Exception as e:
                self.logger.error(f"Error sending message: {e}")
                self.close()
        else:
            self.logger.error("Socket is not connected.")

    def receive_messages(self):
        """Receives messages from the telemetry socket and processes them."""
        if not self.telemetry_sock:
            self.logger.error("Telemetry socket is not connected.")
            return

        self.logger.info("Starting to receive telemetry data.")
        try:
            while True:
                data = self.telemetry_sock.recv(4096).decode('utf-8')
                if not data:
                    self.logger.warning("No data received. Closing telemetry connection.")
                    break
                self.buffer += data
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    try:
                        message = json.loads(line)
                        self.logger.debug(f"Received telemetry message: {message}")
                        self.handle_message(message)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Error decoding JSON data: {e}")
        except Exception as e:
            self.logger.error(f"Error receiving telemetry data: {e}")
        finally:
            self.logger.info("Closing telemetry connection.")
            self.close()

    def receive_events(self):
        """Receives messages from the event socket and processes them."""
        if not self.events_sock:
            self.logger.error("Event socket is not connected.")
            return

        self.logger.info("Starting to receive event data.")
        try:
            while True:
                data = self.events_sock.recv(4096).decode('utf-8')
                if not data:
                    self.logger.warning("No data received. Closing event connection.")
                    break
                self.buffer += data
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    try:
                        message = json.loads(line)
                        self.logger.debug(f"Received event message: {message}")
                        self.handle_event(message)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Error decoding JSON data: {e}")
        except Exception as e:
            self.logger.error(f"Error receiving event data: {e}")
        finally:
            self.logger.info("Closing event connection.")
            self.close()

    def handle_message(self, message):
        """Processes incoming telemetry messages."""
        self.logger.debug(f"Processing message: {message}")
        if "steering_angle" in message and "throttle" in message:
            self.on_telemetry(message)
        else:
            self.logger.warning(f"Unknown message received: {message}")

    def handle_event(self, message):
        self.logger.debug(f"Processing event message: {message}")
        if "event" in message:
            event = message["event"]
            self.logger.info(f"Event received: {event}")
            if event == "episode_metrics":
                self.on_episode_metrics(message)
            elif event == "episode_events":
                self.on_episode_events(message)
            elif event == "episode_event":
                self.on_episode_event(message)
            elif event == "sim_paused":
                self.on_sim_paused()
            elif event == "sim_resumed":
                self.on_sim_resumed()
            elif event == "episode_started":
                self.on_episode_started()
            elif event == "episode_ended":
                self.on_episode_ended()
            else:
                self.logger.warning(f"Unknown event: {event}")
        else:
            self.logger.warning(f"Event message without 'event' field: {message}")

    def on_telemetry(self, data):
        """Processes telemetry data and triggers control commands."""
        self.logger.debug(f"Type of data: {type(data)}, Content of data: {data}")

        if isinstance(data, str):
            try:
                data = json.loads(data)
                self.logger.debug(f"Data after json.loads: Type {type(data)}, Content: {data}")
            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding telemetry JSON data: {e}")
                return

        required_keys = ["pos_x", "pos_y", "pos_z", "steering_angle", "throttle", "lap", "sector", "speed", "cte",
                         "next_cte"]
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            self.logger.error(f"Missing keys in telemetry data: {missing_keys}")
            return

        try:
            image_base64 = data.get("image", "")
            image = None
            if image_base64:
                if len(image_base64) > 0:
                    try:
                        image_bytes = base64.b64decode(image_base64)
                        image = Image.open(io.BytesIO(image_bytes))
                        self.logger.debug("Image processed from telemetry data.")
                    except Exception as e:
                        self.logger.error(f"Error decoding or opening the image: {e}")
                        image = None
                else:
                    self.logger.warning("Empty image data received.")
            else:
                self.logger.warning("No image data received in telemetry.")

            observation = UdacityObservation(
                input_image=image,
                semantic_segmentation=None,
                position=(float(data["pos_x"]), float(data["pos_y"]), float(data["pos_z"])),
                steering_angle=float(data.get("steering_angle", 0.0)),
                throttle=float(data.get("throttle", 0.0)),
                lap=int(data.get('lap', 0)),
                sector=int(data.get('sector', 0)),
                speed=float(data.get("speed", 0.0)) * 3.6,  # m/s to km/h
                cte=float(data.get("cte", 0.0)),
                next_cte=float(data.get("next_cte", 0.0)),
                time=int(time.time() * 1000)
            )

            self.sim_state['observation'] = observation
            self.send_control()

        except Exception as e:
            self.logger.error(f"Error processing telemetry data: {e}")
            return

    def send_pause(self):
        pause_message = {
            "command": "pause_sim"
        }
        self.logger.debug(f"Prepared pause message: {pause_message}")
        self.send_message(pause_message, self.events_sock)

    def send_resume(self):
        resume_message = {
            "command": "resume_sim"
        }
        self.logger.debug(f"Prepared resume message: {resume_message}")
        self.send_message(resume_message, self.events_sock)

    def send_track(self, track, weather, daytime):
        start_episode_message = {
            "command": "start_episode",
            "track_name": track,
            "weather_name": weather,
            "daytime_name": daytime
        }
        self.logger.debug(f"Prepared start episode message: {start_episode_message}")
        self.send_message(start_episode_message, self.events_sock)

    def send_spawn_objects(self, objects: List[ObjectInterface]):
        for object in objects:
            send_message = object.GetMessage()
            self.logger.debug(f"Prepared spawn cars message: {send_message}")
            self.send_message(send_message, self.spawner_sock)

    def send_Traffic_Light(self, objects: List[TrafficLightInterface]):
        for object in objects:
            send_message = object.GetMessage()
            self.logger.debug(f"Prepared spawn cars message: {send_message}")
            self.send_message(send_message, self.events_sock)

    def on_sim_paused(self):
        self.sim_state['sim_state'] = SimStates.PAUSED

    def on_sim_resumed(self):
        self.sim_state['sim_state'] = SimStates.RUNNING

    def on_episode_metrics(self, data):
        self.logger.info(f"Episode metrics: {data}")
        self.sim_state['episode_metrics'] = data

    def on_episode_events(self, data):
        self.logger.info(f"Episode events: {data}")
        self.sim_state['events'] += [data]

    def on_episode_event(self, data):
        self.logger.info(f"Episode event: {data}")
        self.sim_state['events'] += [data]

    def on_episode_started(self):
        self.sim_state['track_set'] = True
        self.logger.info("Track was set successfully.")

    def on_episode_ended(self):
        self.logger.info("Episode ended.")

    def listen_for_telemetry(self):
        """Starts the telemetry listener in a separate thread."""
        self.logger.info("Starting telemetry listener thread.")
        telemetry_thread = threading.Thread(target=self.receive_messages, daemon=True)
        telemetry_thread.start()

    def listen_for_events(self):
        """Starts the event listener in a separate thread."""
        self.logger.info("Starting event listener thread.")
        events_thread = threading.Thread(target=self.receive_events, daemon=True)
        events_thread.start()

    def start(self):
        """Starts the connections and the telemetry listener."""
        self.running = True
        self.logger.info("Starting UdacityExecutor.")
        self.connect_to_server()
        self.listen_for_telemetry()
        self.listen_for_events()

    def close(self):
        """Closes the command and telemetry sockets."""
        self.running = False
        self.logger.info("Closing sockets.")
        if self.command_sock:
            self.command_sock.close()
            self.logger.info("Command socket closed.")
        if self.telemetry_sock:
            self.telemetry_sock.close()
            self.logger.info("Telemetry socket closed.")
        if self.events_sock:
            self.events_sock.close()
            self.logger.info("Event socket closed.")
        if self.spawner_sock:
            self.spawner_sock.close()
            self.logger.info("CarSpawner socket closed.")


if __name__ == '__main__':
    print("Starting UdacityExecutor")
    sim_executor = UdacityExecutor()
    sim_executor.start()
    # sim_executor.send_track(track="lake", daytime="day", weather="sunny")

    #sim_executor.send_spawn_objects(objects)

    test = [
        #MovingObject("Car1", "Human", 2, 1, [0,0,0], [1, 1, 1], [0, 0, 0], "Waypoints Walker", "Road"),
        MovingObject("Car1", "CarBlue", 5, 1, [2, 0.4, 0], [1, 1, 1], [0, 0, 0], "Waypoints 2 Car", "Road", 0),
        MovingObject("Car2", "CarRed", -5, 5, [2, 0.4, 0], [1, 1, 1], [0, 0, 0], "Waypoints 2 Car", "Road", 25),
    ]
    sim_executor.send_spawn_objects(test)
    traffic = [
        # TrafficLightCommand("Light1", "Green"),
        # TrafficLightCommand("Car2", "Yellow"),

        ControlTrafficManager("LightManager", [{"Name":"Rechts", "TrafficLights": ["Car", "Car3"], "PhaseStartTime": 2, "PhaseActiveTime": 5, "PhaseEndTime": 2}, {"Name":"Geradeaus", "TrafficLights": ["Car2"], "PhaseStartTime": 2, "PhaseActiveTime": 10, "PhaseEndTime": 2}], 1)
    ]
    sim_executor.send_Traffic_Light(traffic)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sim_executor.close()
        print("UdacityExecutor stopped")
