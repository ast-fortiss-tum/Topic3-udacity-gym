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

class SimStates(Enum):
    RUNNING = 'running'
    STOPPED = 'stopped'
    PAUSED = 'paused'
    RESUMED = 'resumed'

class UdacityExecutor:
    def __init__(self, host='127.0.0.1'):
        """Initializes the executor with host and ports for command and telemetry connections."""
        self.host = host

        # Ports for Unity or Build version
        # If running in Unity:
        # self.command_port = 55001
        # self.telemetry_port = 56042
        # self.events_port = 54000

        # If running the Build:
        self.command_port = 55002
        self.telemetry_port = 56043
        self.events_port = 54001
        self.command_sock = None
        self.telemetry_sock = None
        self.events_sock = None
        self.running = False
        self.sim_state = get_simulator_state()
        self.logger = CustomLogger(str(self.__class__))
        self.buffer = ''
        self.telemetry_lock = threading.Lock()
        self.logger.info("UdacityExecutor initialized.")

    def connect_to_server(self):
        """Attempts to connect to the command and telemetry servers within a timeout period."""
        self.logger.info("Attempting to connect to the server.")
        timeout = 60
        start_time = time.time()
        while time.time() - start_time < timeout and (not self.command_sock or not self.telemetry_sock or not self.events_sock):

            try:
                # Connect to the command server
                self.command_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.command_sock.connect((self.host, self.command_port))
                self.logger.info(f"Connected to the Command server on {self.host}:{self.command_port}.")
                print(f"Connected to the Command server on {self.host}:{self.command_port}.")

            except Exception as e:
                self.logger.error(f"Error connecting to the Command server on port {self.command_port}: {e}")
                print(f"Error connecting to the Command server on port {self.command_port}: {e}")
                self.command_sock = None

            try:
                # Connect to the telemetry server
                self.telemetry_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.telemetry_sock.connect((self.host, self.telemetry_port))
                self.logger.info(f"Connected to the Telemetry server on {self.host}:{self.telemetry_port}.")
                print(f"Connected to the Telemetry server on {self.host}:{self.telemetry_port}.")

            except Exception as e:
                self.logger.error(f"Error connecting to the Telemetry server on port {self.telemetry_port}: {e}")
                print(f"Error connecting to the Telemetry server on port {self.telemetry_port}: {e}")
                self.telemetry_sock = None

            try:
                # Connect to the events server
                self.events_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.events_sock.connect((self.host, self.events_port))
                self.logger.info(f"Connected to the Telemetry server on {self.host}:{self.events_port}.")
                print(f"Connected to the Telemetry server on {self.host}:{self.events_port}.")

            except Exception as e:
                self.logger.error(f"Error connecting to the Telemetry server on port {self.events_port}: {e}")
                print(f"Error connecting to the Telemetry server on port {self.events_port}: {e}")
                self.events_sock = None

            if not self.command_sock or not self.telemetry_sock or  not self.events_sock :
                self.logger.warning("Failed to connect to the servers. Retrying...")
                print("Failed to connect to the servers.")
                self.close()
                time.sleep(2)

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
            self.logger.debug(f"Control data prepared: {control_data}")
            self.send_message(control_data,self.command_sock)
    def send_message(self, message, currentSocket):
        """Sends a message to the command server."""
        self.logger.debug(f"Attempting to send message: {message}")
        if currentSocket:
            try:
                data = json.dumps(message).encode('utf-8') + b'\n'
                currentSocket.sendall(data)
                self.logger.info(f"Message sent: {message}")
            except Exception as e:
                self.logger.error(f"Error sending commands: {e}")
                self.close()



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
        """Receives messages from the events socket and processes them."""
        if not self.events_sock:
            self.logger.error("Events socket is not connected.")
            return

        self.logger.info("Starting to receive event data.")
        try:
            while True:
                data = self.events_sock.recv(4096).decode('utf-8')
                if not data:
                    self.logger.warning("No data received. Closing events connection.")
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
            self.logger.info("Closing events connection.")
            self.close()


    def handle_message(self, message):
        """Handles incoming telemetry messages."""
        self.logger.debug(f"Handling message: {message}")
        if "steering_angle" in message and "throttle" in message:
            self.on_telemetry(message)
        else:
            self.logger.warning(f"Unknown message received: {message}")

    def handle_event(self, message):
        self.logger.debug(f"Handling event message: {message}")
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
            else:
                self.logger.warning(f"Unknown event: {event}")
        else:
            self.logger.warning(f"Event message without 'event' field: {message}")

    def on_telemetry(self, data):
        """Processes telemetry data and triggers control commands."""
        # Ensure the incoming data contains an image and necessary fields.
        self.logger.info("Processing telemetry data.")
        try:
            image_base64 = data.get("image", "")
            image = None
            if image_base64:
                if len(image_base64) > 0:  # Check if the image data is not empty
                    try:
                        # Decode and open the image
                        image_bytes = base64.b64decode(image_base64)
                        image = Image.open(io.BytesIO(image_bytes))
                        self.logger.debug("Image processed from telemetry data.")
                    except Exception as e:
                        self.logger.error(f"Failed to decode or open image: {e}")
                        image = None  # If the image is invalid, set to None
                else:
                    self.logger.warning("Received empty image data.")

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
            # Sending control
            self.send_control()

            if self.sim_state.get('paused', False):
                self.send_pause()
            else:
                self.send_resume()
            track_info = self.sim_state.get('track', None)
            if track_info:
                track, weather, daytime = track_info['track'], track_info['weather'], track_info['daytime']
                self.send_track(track, weather, daytime)
                self.sim_state['track'] = None

        except Exception as e:
            self.logger.error(f"Error processing telemetry data: {e}")

    def send_pause(self):
        pause_message = {
            "command": "pause_sim"
        }
        self.logger.debug(f"Pause message prepared: {pause_message}")
        self.send_message(pause_message,self.events_sock)

    def send_resume(self):
        resume_message = {
            "command": "resume_sim"
        }
        self.logger.debug(f"resume message prepared: {resume_message}")
        self.send_message(resume_message, self.events_sock)

    def send_track(self, track, weather, daytime):
        end_episode_message = {
            "command": "end_episode"
        }
        start_episode_message = {
            "command": "start_episode",
            "track_name": track,
            "weather_name": weather,
            "daytime_name": daytime,
        }
        self.logger.debug(f"resume message prepared: {end_episode_message}")
        self.logger.debug(f"resume message prepared: {start_episode_message}")
        self.send_message(end_episode_message,self.events_sock)
        self.send_message(start_episode_message,self.events_sock)

    def on_sim_paused(self):
        self.sim_state['sim_state'] = 'paused'
        #self.sim_state['sim_state'] = SimStates.PAUSED


    def on_sim_resumed(self):
        self.sim_state['sim_state'] = 'running'

    def on_episode_metrics(self, data):
        self.logger.info(f"episode metrics {data}")
        self.sim_state['episode_metrics'] = data

    def on_episode_events(self, data):
        self.logger.info(f"Episode events: {data}")
        self.sim_state['events'] += [data]

    def on_episode_event(self, data):
        self.logger.info(f"Episode event: {data}")
        self.sim_state['events'] += [data]


    def listen_for_telemetry(self):
        """Starts the telemetry listener in a separate thread."""
        self.logger.info("Starting telemetry listener thread.")
        telemetry_thread = threading.Thread(target=self.receive_messages, daemon=True)
        telemetry_thread.start()

    def listen_for_events(self):
        """Starts the events listener in a separate thread."""
        self.logger.info("Starting events listener thread.")
        telemetry_thread = threading.Thread(target=self.receive_events, daemon=True)
        telemetry_thread.start()

    def start(self):
        """Starts the connections and telemetry listener."""
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


if __name__ == '__main__':
    print("running")
    sim_executor = UdacityExecutor()
    sim_executor.start()
    print("started")
