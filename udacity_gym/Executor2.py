import base64
import time
from io import BytesIO
from multiprocessing import Process
from threading import Thread
import threading
import PIL
import eventlet
import json
eventlet.monkey_patch()
import numpy as np
from PIL import Image, UnidentifiedImageError
from .action import UdacityAction
from .logger import CustomLogger
from .observation import UdacityObservation
import socket

#TODO: More updates when the server side is ready to handle connections
class UdacityExecutor:
    # TODO: avoid cycles

    def __init__(
            self,
            host: str = "127.0.0.1",
            port: int = 4567,
    ):
        # Simulator network settings
        self.host = host
        self.port = port
        self.client_socket = None
        self.running = False
        # Simulator logging
        self.logger = CustomLogger(str(self.__class__))
        # Simulator
        from .simulator import simulator_state
        self.sim_state = simulator_state
        self.handlers = {
            "car_telemetry": self.on_telemetry,
            "episode_metrics": self.on_episode_metrics,
            "episode_events": self.on_episode_events,
            "episode_event": self.on_episode_event,
            "sim_paused": self.on_sim_paused,
            "sim_resumed": self.on_sim_resumed
        }

    def connect(self):
        self.logger.info("Trying to Connect to the server")
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.logger.info(f"Connected to server at {self.host}:{self.port}")
            threading.Thread(target=self.listen_for_messages, daemon=True).start()
        except Exception as e:
            self.logger.info(f"Failed to connect to server: {e}")

    def listen_for_messages(self):
        while self.sim_state == 'running':
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    self.handle_message(message)
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.sim_state = 'stopped'

    def handle_message(self, message):
        try:
            message_data = json.loads(message)  # Parse JSON message
            message_type = message_data.get("type")

            if message_type in self.handlers:
                # Call the corresponding handler method
                self.handlers[message_type](message_data)
            else:
                print(f"Unknown message type: {message_type}")
        except json.JSONDecodeError:
            print("Failed to decode message. Expected JSON format.")
        except Exception as e:
            print(f"Error handling message: {e}")



    def on_sim_paused(self, data):
        self.sim_state['sim_state'] = 'paused'

    def on_sim_resumed(self, data):
            # TODO: change 'running' with ENUM
            self.sim_state['sim_state'] = 'running'

    def on_episode_metrics(self, data):
        try:
            data_js = json.loads(data)
            self.logger.info(f"episode metrics {data_js}")
            self.sim_state['episode_metrics'] = data_js
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON message: {e}")

    def on_episode_events(self, data):
        try:
            data_js = json.loads(data)
            self.logger.info(f"Episode events: {data_js}")
            self.sim_state['events'] += [data_js]
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON message: {e}")

    def on_episode_event(self, data):
        try:
            data_js = json.loads(data)
            self.logger.info(f"Episode event: {data_js}")
            self.sim_state['events'] += [data_js]
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON message: {e}")

    def on_telemetry(self, data):


        # self.logger.info(f"Received data from udacity client: {data}")
        # TODO: check data image, verify from sender that is not empty
        # TODO: Check image
        try:
            # Decode JSON data
            data = json.loads(data.decode('utf-8'))
            # Process the image data
            input_image = None
            if "image" in data:
                try:
                    input_image = Image.open(BytesIO(base64.b64decode(data["image"])))
                except UnidentifiedImageError:
                    print("image could not be decoded.")
            semantic_segmentation = None
            observation = UdacityObservation(
                input_image=input_image,
                semantic_segmentation=semantic_segmentation,
                position=(float(data["pos_x"]), float(data["pos_y"]), float(data["pos_z"])),
                steering_angle=float(self.sim_state.get('action', None).steering_angle),
                throttle=float(self.sim_state.get('action', None).throttle),
                lap=int(data['lap']),
                sector=int(data['sector']),
                speed=float(data["speed"]) * 3.6,  # conversion m/s to km/h
                cte=float(data["cte"]),
                next_cte=float(data["next_cte"]),
                time=int(time.time() * 1000)
            )
            self.sim_state['observation'] = observation
            # Sending control
            self.send_control()#TODO: Check this function
            if self.sim_state.get('paused', False):
                self.send_pause()#TODO: Check this function
            else:
                self.send_resume()#TODO: Check this function
            track_info = self.sim_state.get('track', None)
            if track_info:
                track, weather, daytime = track_info['track'], track_info['weather'], track_info['daytime']
                self.send_track(track, weather, daytime)#TODO: Check this function
                self.sim_state['track'] = None
        except (json.JSONDecodeError, KeyError) as e:
            print("Error decoding JSON data:", e)

    def send_control(self) -> None:
        action: UdacityAction = self.sim_state.get('action', None)
        if action:
            control_data = {
                "command": "send_control",
                "steering_angle": str(action.steering_angle),
                "throttle": str(action.throttle),
            }
            json_data = json.dumps(control_data) + "\n"
            try:
                self.client_socket.sendall(json_data.encode('utf-8'))
                self.logger.info("Sent control action to server.")
            except BrokenPipeError:
                self.logger.error("Connection to server lost.")


    def send_pause(self):
        pause_message = {
            "command": "pause_sim"
        }
        json_data = json.dumps(pause_message) + "\n"
        try:
            self.client_socket.sendall(json_data.encode('utf-8'))
            self.logger.info("Sent pause command to server.")
        except BrokenPipeError:
            self.logger.error("Connection to server lost.")


    def send_resume(self):
        resume_message = {
            "command": "resume_sim"
        }
        json_data = json.dumps(resume_message) + "\n"
        try:
            self.client_socket.sendall(json_data.encode('utf-8'))
            self.logger.info("Sent resume command to server.")
        except BrokenPipeError:
            self.logger.error("Connection to server lost.")

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
        json_data_end_message = json.dumps(end_episode_message) + "\n"
        json_data_start_episode_message = json.dumps(start_episode_message) + "\n"
        try:
            self.client_socket.sendall(json_data_end_message.encode('utf-8'))
            self.logger.info("Sent end episode command to server.")
            self.client_socket.sendall(json_data_start_episode_message.encode('utf-8'))
            self.logger.info("Sent start episode command to server.")
        except BrokenPipeError:
            self.logger.error("Connection to server lost.")

    def start(self):
        self.running = True
        self.connect()


    def close(self):
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
                self.logger.info("Connection closed.")
            except Exception as e:
                self.logger.error(f"Error closing connection: {e}")


if __name__ == '__main__':
    sim_executor = UdacityExecutor()
    sim_executor.start()






















if __name__ == '__main__':
    sim_executor = UdacityExecutor()
    sim_executor.start()
