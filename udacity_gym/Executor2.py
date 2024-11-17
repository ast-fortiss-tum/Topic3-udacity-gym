import base64
import io
import socket
import threading
import json
import time
from PIL import Image
from udacity_gym.observation import UdacityObservation
from udacity_gym.logger import CustomLogger
from udacity_gym.global_manager import get_simulator_state
from enum import Enum


# Define simulation states with Enum
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
            telemetry_port: int = 56042,
            events_port: int = 54001,
            car_spawner_port: int = 57001,  # Neuer Port für den CarSpawner
    ):
        """Initializes the executor with host and ports for command and telemetry connections."""
        self.host = host
        self.command_port = command_port
        self.telemetry_port = telemetry_port
        self.events_port = events_port
        self.car_spawner_port = car_spawner_port  # Speichert den neuen Port
        self.command_sock = None
        self.telemetry_sock = None
        self.events_sock = None
        self.car_spawner_sock = None  # Neuer Socket für den CarSpawner
        self.running = False
        self.sim_state = get_simulator_state()
        self.logger = CustomLogger(str(self.__class__))
        self.buffer = ''
        self.telemetry_lock = threading.Lock()
        self.logger.info("UdacityExecutor initialized.")
        self.spawn_cars_sent = False

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
                if not self.car_spawner_sock:
                    self.car_spawner_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.car_spawner_sock.connect((self.host, self.car_spawner_port))
                    self.logger.info(f"Connected to CarSpawner server at {self.host}:{self.car_spawner_port}.")
            except Exception as e:
                self.logger.error(f"Error connecting to the CarSpawner server on port {self.car_spawner_port}: {e}")
                self.car_spawner_sock = None
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
        self.logger.info("Sending control commands to the simulator.")
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
        self.logger.info("Processing telemetry data.")
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
            self.logger.info("Telemetry data processed successfully.")
            # Send control commands
            self.send_control()

            # Spawn cars nach dem ersten Empfang von Telemetriedaten
            if not self.spawn_cars_sent:
                self.logger.info("First telemetry received, spawning other cars.")
                number_of_cars = 2
                start_positions = [2, 4]
                self.send_spawn_cars(number_of_cars, start_positions)
                self.spawn_cars_sent = True  # Setze das Flag auf True, damit die Autos nur einmal gespawnt werden

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
        # end_episode_message = {
           # "command": "end_episode"
        # }
        start_episode_message = {
            "command": "start_episode",
            "track_name": track,
            "weather_name": weather,
            "daytime_name": daytime
        }
        # self.logger.debug(f"Prepared end episode message: {end_episode_message}")
        self.logger.debug(f"Prepared start episode message: {start_episode_message}")
        # self.send_message(end_episode_message, self.events_sock)
        self.send_message(start_episode_message, self.events_sock)

    def send_spawn_cars(self, number_of_cars, start_positions):
        spawn_cars_message = {
            "command": "spawn_cars",
            "number_of_cars": number_of_cars,
            "start_positions": start_positions
        }
        print(f"Prepared spawn cars message: {spawn_cars_message}")
        self.logger.debug(f"Prepared spawn cars message: {spawn_cars_message}")
        self.send_message(spawn_cars_message, self.car_spawner_sock)  # Sende über den neuen Socket

    def on_sim_paused(self):
        self.sim_state['sim_state'] = SimStates.PAUSED  # Use Enum instead of string

    def on_sim_resumed(self):
        self.sim_state['sim_state'] = SimStates.RUNNING  # Use Enum instead of string

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
        if self.car_spawner_sock:
            self.car_spawner_sock.close()
            self.logger.info("CarSpawner socket closed.")


if __name__ == '__main__':
    print("Starting UdacityExecutor")
    sim_executor = UdacityExecutor()
    sim_executor.start()
    sim_executor.send_track(track="lake", daytime="day", weather="sunny")

    # Warte, bis der Simulator die Strecke gesetzt hat
    while not sim_executor.sim_state.get('track_set', False):
        print("Waiting for the simulator to set the track...")
        time.sleep(1)

    # Jetzt wird send_spawn_cars in on_telemetry aufgerufen

    try:
        # Hauptschleife
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sim_executor.close()
        print("UdacityExecutor stopped")
