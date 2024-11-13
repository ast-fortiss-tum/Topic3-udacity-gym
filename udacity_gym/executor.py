import base64
import io
import socket
import threading
import json
import time
import csv
import pathlib

from PIL import Image

from udacity_gym.observation import UdacityObservation
from udacity_gym.logger import CustomLogger
from udacity_gym.global_manager import get_simulator_state

class UdacityExecutorAlt:
    def __init__(
            self,
            host: str ='127.0.0.1',
            command_port: int = 55002,
            telemetry_port: int = 56043,
    ):
        """Initializes the executor with host and ports for command and telemetry connections."""
        self.host = host
        self.command_port = command_port
        self.telemetry_port = telemetry_port
        self.command_sock = None
        self.telemetry_sock = None
        self.sim_state = get_simulator_state()
        self.logger = CustomLogger(str(self.__class__))
        self.buffer = ''
        self.telemetry_lock = threading.Lock()
        self.logger.info("UdacityExecutor initialized.")

        # Initialize CSV for latency logging
        self.latency_file = f"udacity_dataset_lake_12_12_2\lake_sunny_day\latency_log.csv"
        with open(self.latency_file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "event", "latency"])

    def connect_to_server(self):
        """Attempts to connect to the command and telemetry servers within a timeout period."""
        self.logger.info("Attempting to connect to the server.")
        timeout = 60
        start_time = time.time()
        while time.time() - start_time < timeout and (not self.command_sock or not self.telemetry_sock):

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

            if not self.command_sock or not self.telemetry_sock:
                self.logger.warning("Failed to connect to both servers. Retrying...")
                print("Failed to connect to both servers.")
                self.close()
                time.sleep(2)

    def log_latency(self, event, timestamp):
        """Logs latency data to a CSV file."""
        with open(self.latency_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, event, time.time() - timestamp])

    def send_message(self, message):
        """Sends a message to the command server."""
        self.logger.debug(f"Attempting to send message: {message}")
        if self.command_sock:
            try:
                timestamp = time.time()
                data = json.dumps(message).encode('utf-8') + b'\n'
                self.command_sock.sendall(data)
                self.log_latency('send', timestamp)
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
                timestamp = time.time()
                data = self.telemetry_sock.recv(4096).decode('utf-8')
                if not data:
                    self.logger.warning("No data received. Closing telemetry connection.")
                    break
                self.buffer += data
                self.log_latency('receive', timestamp)
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

    def handle_message(self, message):
        """Handles incoming telemetry messages."""
        self.logger.debug(f"Handling message: {message}")
        if "steering_angle" in message and "throttle" in message:
            self.on_telemetry(message)
        else:
            self.logger.warning(f"Unknown message received: {message}")

    def on_telemetry(self, data):
        """Processes telemetry data and triggers control commands."""
        self.logger.info("Processing telemetry data.")
        try:
            image_base64 = data.get("image", "")
            if image_base64:
                image_bytes = base64.b64decode(image_base64)
                image = Image.open(io.BytesIO(image_bytes))
                self.logger.debug("Image processed from telemetry data.")
            else:
                image = None

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
            self.send_control()

        except Exception as e:
            self.logger.error(f"Error processing telemetry data: {e}")

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
            self.send_message(control_data)

    def listen_for_telemetry(self):
        """Starts the telemetry listener in a separate thread."""
        self.logger.info("Starting telemetry listener thread.")
        telemetry_thread = threading.Thread(target=self.receive_messages, daemon=True)
        telemetry_thread.start()

    def start(self):
        """Starts the connections and telemetry listener."""
        self.logger.info("Starting UdacityExecutor.")
        self.connect_to_server()
        self.listen_for_telemetry()

    def close(self):
        """Closes the command and telemetry sockets."""
        self.logger.info("Closing sockets.")
        if self.command_sock:
            self.command_sock.close()
            self.logger.info("Command socket closed.")
        if self.telemetry_sock:
            self.telemetry_sock.close()
            self.logger.info("Telemetry socket closed.")

if __name__ == '__main__':
    print("running")
    sim_executor = UdacityExecutorAlt()
    sim_executor.start()
    print("started")
