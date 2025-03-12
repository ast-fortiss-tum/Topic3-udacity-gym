import json
import pathlib
import random
import time
import tqdm
from udacity_gym import UdacitySimulator, UdacityGym, UdacityAction
from udacity_gym.agent import PIDUdacityAgent  # oder einen anderen Agenten-Typ
from udacity_gym.agent_callback import LogObservationCallback, PauseSimulationCallback, ResumeSimulationCallback

import csv
import statistics
import pandas as pd
import matplotlib.pyplot as plt

from udacity_gym.extras.Objects.MovingObject import MovingObject
from udacity_gym.extras.Objects.StaticBlock import StaticBlock

if __name__ == '__main__':

    # ------------------ Konfiguration ------------------
    host = "127.0.0.1"
    command_port = 55002
    telemetry_port = 56002
    events_port = 57002
    other_cars_port = 58002
    simulator_exe_path = r"C:\Source\Auto\Windows Build\self_driving_car_nanodegree_program.exe"
    assert pathlib.Path(simulator_exe_path).exists(), f"Simulator binary not found at {simulator_exe_path}"

    track = "city"
    daytime = "day"
    weather = "sunny"

    # ------------------ Simulator und Environment erstellen ------------------
    simulator = UdacitySimulator(
        sim_exe_path=simulator_exe_path,
        host=host,
        command_port=command_port,
        telemetry_port=telemetry_port,
        events_port=events_port,
        other_cars_port=other_cars_port
    )

    env = UdacityGym(simulator=simulator)
    simulator.start()
    observation, _ = env.reset(track=track, weather=weather, daytime=daytime)

    # Warte, bis das Environment vollständig eingerichtet ist
    while not observation or not observation.is_ready():
        observation = env.observe()
        print("Waiting for environment to set up...")
        time.sleep(1)

    # ------------------ Spawn von mehreren Autos und zugehörigen Agenten ------------------
    num_cars_to_spawn = 3  # Anzahl der zu spawnenden Autos
    car_agents = {}  # Dictionary: Schlüssel = Car-Name, Wert = Agent
    car_objects = []  # Liste der MovingObject-Instanzen für den Spawn-Befehl
    possible_car_prefabs = ["Objects/CarBlue", "Objects/CarRed", "Objects/CarBlack"]

    for i in range(num_cars_to_spawn):
        car_name = f"Car_{i + 1}"
        prefab = random.choice(possible_car_prefabs)
        # Parameter (Platzhalter – passe diese Werte an deine Bedürfnisse an)
        spawn_point = 5  # z. B. als Start-Wegpunktindex
        speed = random.uniform(10, 50)
        offset = [0, 0.4, 0]
        scale = [1, 1, 1]
        rotation = [0, 0, 0]
        waypoints = ["MainStreet1", "Smal2", "Smal1 reverse", "MainStreet1"]
        layer = "Road"
        human_behavior = 0  # Beispiel: 0 = kein menschliches Verhalten

        # Erzeuge ein MovingObject für das Auto
        moving_obj = MovingObject(car_name, prefab, spawn_point, speed, offset, scale, rotation, waypoints, layer,
                                  human_behavior)
        car_objects.append(moving_obj)

        # Erzeuge einen Agenten, der dieses Auto steuern soll (hier ein PID-Agent)
        agent = PIDUdacityAgent(
            kp=0.05, kd=0.8, ki=0.000001,
            before_action_callbacks=[],
            after_action_callbacks=[]
        )
        car_agents[car_name] = agent

    # Sende den Spawn-Befehl an den Simulator, sodass alle Autos erstellt werden
    env.setothercars(car_objects)
    print(f"Spawned {num_cars_to_spawn} cars.")

    # ------------------ Haupt-Simulationsloop ------------------
    # Wir gehen hier davon aus, dass env.get_other_observations() ein Dictionary zurückgibt,
    # in dem die Beobachtungen der gespawnten Autos unter ihrem Namen (oder einer eindeutigen carId)
    # abgelegt werden. (Diese Methode muss ggf. in UdacityGym implementiert werden.)
    while True:
        # Beobachtung des Ego-Autos (falls benötigt)
        observation = env.observe()

        # Beobachtungen der anderen Autos abrufen
        other_observations = env.get_other_observations()  # Erwartet: { car_name: observation, ... }

        # Für jedes gespawnte Auto: Aktion berechnen und Befehl senden
        for car_name, agent in car_agents.items():
            if car_name in other_observations:
                car_obs = other_observations[car_name]
                # Der Agent berechnet die Aktion anhand der Beobachtung
                action = agent(car_obs)
                # Erstelle den Steuerbefehl – hier wird angenommen, dass die Observation auch ein Feld car_id enthält.
                control_command = {
                    "command": "send_control",
                    "carId": car_obs.car_id,  # oder nutze den car_name, falls dies als ID genutzt wird
                    "steering_angle": action.steering_angle,
                    "throttle": action.throttle
                }
                # Sende den Steuerbefehl an den Simulator (die Methode send_control muss in UdacityGym implementiert sein)
                env.send_control(control_command)
            else:
                print(f"No observation received yet for {car_name}.")
        time.sleep(0.01)  # Passe die Schleifenfrequenz nach Bedarf an
