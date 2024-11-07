import base64
import io
import socket
import threading
import json
import time

from PIL import Image

from udacity_gym.action import UdacityAction
from udacity_gym.observation import UdacityObservation
from udacity_gym.logger import CustomLogger
from udacity_gym.global_manager import get_simulator_state
from udacity_gym.agent import PIDUdacityAgent


class UdacityExecutor:
    def __init__(self, host='127.0.0.1'):
        self.host = host

        """If Running in Unity"""
        # self.command_port = 55001
        # self.telemetry_port = 56042

        """If Running the Build"""
        self.command_port = 55002
        self.telemetry_port = 56043

        self.command_sock = None
        self.telemetry_sock = None
        self.sim_state = get_simulator_state()
        self.logger = CustomLogger(str(self.__class__))
        self.buffer = ''
        self.agent = PIDUdacityAgent(kp=0.05, kd=0.8, ki=0.000001)
        self.telemetry_lock = threading.Lock()

    def connect_to_server(self):
        """Versucht, sich mit einem der Server zu verbinden (Editor oder Build)."""
        # Versuche, eine Verbindung zu den Command-Server-Ports herzustellen
        timeout = 60
        start_time = time.time()
        while time.time() - start_time < timeout and (not self.command_sock or not self.telemetry_sock) :

            try:
                self.command_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.command_sock.connect((self.host, self.command_port))
                print(f"Verbunden mit dem Command-Server auf {self.host}:{self.command_port}.")



            except Exception as e:
                print(f"Fehler beim Verbinden mit dem Command-Server auf Port {self.command_port}: {e}")
                self.command_sock = None

            # Versuche, eine Verbindung zu den Telemetry-Server-Ports herzustellen


            try:
                self.telemetry_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.telemetry_sock.connect((self.host, self.telemetry_port))
                print(f"Verbunden mit dem Telemetry-Server auf {self.host}:{self.telemetry_port}.")



            except Exception as e:
                print(f"Fehler beim Verbinden mit dem Telemetry-Server auf Port {self.telemetry_port}: {e}")
                self.telemetry_sock = None

            # Überprüfe, ob eine Verbindung hergestellt wurde
            if not self.command_sock or not self.telemetry_sock:
                print("Konnte keine Verbindung zu beiden Servern herstellen.")
                self.close()
                time.sleep(2)

    def send_message(self, message):
        """Sendet eine Nachricht über den Command-Socket."""
        if self.command_sock:
            try:
                data = json.dumps(message).encode('utf-8') + b'\n'
                self.command_sock.sendall(data)
                self.logger.info(f"Gesendete Nachricht: {message}")
            except Exception as e:
                self.logger.error(f"Fehler beim Senden von Befehlen: {e}")
                self.close()

    def receive_messages(self):
        """Empfängt Nachrichten vom Telemetry-Socket."""
        if not self.telemetry_sock:
            self.logger.error("Telemetry-Socket ist nicht verbunden.")
            return

        try:
            while True:
                data = self.telemetry_sock.recv(4096).decode('utf-8')
                if not data:
                    self.logger.warning("Keine Daten empfangen. Telemetry-Verbindung wird geschlossen.")
                    break
                self.buffer += data
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    try:
                        message = json.loads(line)
                        self.handle_message(message)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Fehler beim Dekodieren der JSON-Daten: {e}")
        except Exception as e:
            self.logger.error(f"Fehler beim Empfangen von Telemetriedaten: {e}")
        finally:
            self.close()

    def handle_message(self, message):
        """Verarbeitet empfangene Telemetriedaten."""
        if "steering_angle" in message and "throttle" in message:
            self.on_telemetry(message)
        else:
            self.logger.warning(f"Unbekannte Nachricht erhalten: {message}")

    def on_telemetry(self, data):
        """Verarbeitet Telemetriedaten und sendet Steuerbefehle."""
        try:
            image_base64 = data.get("image", "")
            if image_base64:
                image_bytes = base64.b64decode(image_base64)
                image = Image.open(io.BytesIO(image_bytes))
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
                speed=float(data.get("speed", 0.0)) * 3.6,  # m/s zu km/h
                cte=float(data.get("cte", 0.0)),
                next_cte=float(data.get("next_cte", 0.0)),
                time=int(time.time() * 1000)
            )
            print(f"Geschwindigkeit: {observation.speed} km/h")
            self.sim_state['observation'] = observation
            action = self.agent(observation)
            # action = UdacityAction(steering_angle=-0.1, throttle=0.5)
            self.sim_state['action'] = action
            self.sim_state['sim_state'] = 'running'

            # Senden der Steuerbefehle
            self.send_control()
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der Telemetriedaten: {e}")

    def send_control(self):
        """Sendet Steuerbefehle an den Simulator."""
        action = self.sim_state.get('action', None)
        if action:
            control_data = {
                "command": "send_control",
                "steering_angle": action.steering_angle,
                "throttle": action.throttle,
            }
            self.send_message(control_data)

    def listen_for_telemetry(self):
        """Startet den Telemetry-Listener in einem separaten Thread."""
        telemetry_thread = threading.Thread(target=self.receive_messages, daemon=True)
        telemetry_thread.start()

    def send_commands_thread(self):
        """Optional: Ein separater Thread zum kontinuierlichen Senden von Befehlen."""
        # Dies kann genutzt werden, um kontinuierlich Befehle zu senden, falls erforderlich
        pass  # Hier kann zusätzliche Logik hinzugefügt werden

    def start(self):
        """Startet die Verbindungen und Threads."""
        self.connect_to_server()
        self.listen_for_telemetry()
        # Starte einen optionalen Thread zum Senden von Befehlen
        # send_commands_thread = threading.Thread(target=self.send_commands_thread, daemon=True)
        # send_commands_thread.start()

        # Verhindern, dass das Skript sofort beendet wird
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.close()
            print("Skript beendet.")

    def close(self):
        if self.command_sock:
            self.command_sock.close()
        if self.telemetry_sock:
            self.telemetry_sock.close()


if __name__ == '__main__':
    print("running")
    sim_executor = UdacityExecutor()
    sim_executor.start()
    print("started")
