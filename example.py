import json
import pathlib
import random
import time
import tqdm
from udacity_gym import UdacitySimulator, UdacityGym, UdacityAction
from udacity_gym.agent import PIDUdacityAgent, EndToEndLaneKeepingAgent
from udacity_gym.agent_callback import LogObservationCallback, PauseSimulationCallback, ResumeSimulationCallback

import csv
import statistics
import pandas as pd
import matplotlib.pyplot as plt

from udacity_gym.extras.Objects.MovingObject import MovingObject
from udacity_gym.extras.Objects.StaticBlock import StaticBlock

if __name__ == '__main__':

    # Configuration settings
    host = "127.0.0.1"
    command_port = 55002
    telemetry_port = 56002
    events_port = 57002
    other_cars_port = 58002
    # simulator_exe_path = "/home/banana/projects/self-driving-car-sim/Builds/udacity_linux.x86_64"

    # TCP Port
    simulator_exe_path = r"C:\Source\Auto\Windows Build\self_driving_car_nanodegree_program.exe"

    # Io Port
    # simulator_exe_path = r"C:\Source\Auto\beta_simulator_windows\beta_simulator.exe"
    assert pathlib.Path(simulator_exe_path).exists(), f"Simulator binary not found at {simulator_exe_path}"

    # Track settings
    track = "lake"
    daytime = "day"
    weather = "sunny"

    objects = [
        MovingObject("Car1", "Dummy",4, 3, 20, [1,1,1], [0,0,0] ),
        MovingObject("Car1", "Bus", -2, 2, 7, [8, 8, 8], [0, 90, 0]),
        MovingObject("Car1", "Bus", 4, 2, 7, [8, 8, 8], [0, 90, 0]),
        MovingObject("Car1", "Bus", -2, 2, 10, [8, 8, 8], [0, 90, 0]),
        MovingObject("Car1", "Bus", -2, 2, 15, [8, 8, 8], [0, 90, 0]),
        MovingObject("Car1", "Bus", -2, 2, 20, [8, 8, 8], [0, 90, 0]),
        MovingObject("Car1", "Bus", -2, 2, 3, [8, 8, 8], [0, 90, 0]),
        MovingObject("Car1", "CarBlack", 3, 5, 3, [1, 1, 1], [0, 0, 0]),
        MovingObject("Car1", "Bus", -2, 2, 8, [8, 8, 8], [0, 90, 0]),
        MovingObject("Car1", "Dummy", -2, 3, 25, [1, 1, 1], [0, 0, 0]),
        MovingObject("Car1", "Dummy", -2, 3, 28, [1, 1, 1], [0, 0, 0]),

        MovingObject("Car1", "CarBlack", 3, 3, 3, [1, 1, 1], [0, 0, 0]),
        MovingObject("Car1", "CarBlue", 3, 3, 4, [1, 1, 1], [0, 0, 0]),
        MovingObject("Car1", "CarRed", 3, 3, 5, [1, 1, 1], [0, 0, 0]),

        StaticBlock("Block1", "BarricadaNew", 4.5, 7, [2,2,2], [270, 0, 0]),
        StaticBlock("Block2", "House",20.5, -4, [0.1, 0.3, 0.1], [0, 0, 0])
    ]

    log_directory = pathlib.Path(f"udacity_dataset_lake_12_12_2/{track}_{weather}_{daytime}")

    # Creating the simulator wrapper
    simulator = UdacitySimulator(
        sim_exe_path=simulator_exe_path,
        host=host,
        command_port=command_port,
        telemetry_port=telemetry_port,
        events_port=events_port,
        other_cars_port=other_cars_port
    )

    # Creating the gym environment
    env = UdacityGym(
        simulator=simulator,
    )
    simulator.start()
    observation, _ = env.reset(track=f"{track}",
                               weather=f"{weather}",
                               daytime=f"{daytime}")

    # Wait for environment to set up
    while not observation or not observation.is_ready():
        observation = env.observe()
        print("Waiting for environment to set up...")
        time.sleep(1)

    env.setothercars(objects)

    log_observation_callback = LogObservationCallback(log_directory)
    agent = PIDUdacityAgent(
        kp=0.05, kd=0.8, ki=0.000001,
        # kp=0.12, kd=1.2, ki=0.000001,
        before_action_callbacks=[],
        after_action_callbacks=[log_observation_callback],
    )

    #agent = EndToEndLaneKeepingAgent()

    # Interacting with the gym environment
    for _ in tqdm.tqdm(range(5000)):

        spawnNumber = random.randint(1, 1000)
        if spawnNumber == 1:
            spawnDistance = random.uniform(0.5, 30)
            spawnOffset = random.randint(-5, 5 )
            spawnRotation = random.randint(0, 360)
            spawnScale = random.uniform(0.5, 2)
            randomObjects = [StaticBlock("Random", "BarricadaNew", observation.sector + spawnDistance, spawnOffset, [2*spawnScale,2*spawnScale,2*spawnScale], [270, spawnRotation, 0])]
            env.setothercars(randomObjects)
            print("Spawn")
        action = agent(observation)
        last_observation = observation
        observation, reward, terminated, truncated, info = env.step(action)

        while observation.time == last_observation.time:
            observation = env.observe()
            time.sleep(0.0025)

    if info:
        json.dump(info, open(log_directory.joinpath("info.json"), "w"))

    log_observation_callback.save()
    simulator.close()
    env.close()
    print("Experiment concluded.")

    # Integrate the latency calculation and plotting code
    def calculate_latencies(input_csv, output_csv):
        latencies = []

        # Read existing latencies from output_csv if it exists
        if pathlib.Path(output_csv).exists():
            with open(output_csv, 'r') as outfile:
                reader = csv.reader(outfile)
                next(reader)  # Skip header
                for row in reader:
                    if row and row[0]:
                        latencies.append(float(row[0]))

        # Now read new latencies from input_csv
        with open(input_csv, 'r') as infile:
            reader = csv.reader(infile)
            next(reader)  # Skip header

            send_event = None
            for row in reader:
                timestamp, event, _ = float(row[0]), row[1], row[2]

                if event == 'send':
                    send_event = timestamp
                elif event == 'receive' and send_event is not None:
                    # Calculate latency as the difference between send and receive
                    latency = (timestamp - send_event) * 1000  # Convert to milliseconds
                    latencies.append(latency)
                    send_event = None  # Reset for the next send event

        # Calculate average and standard deviation of latencies
        if latencies:
            avg_latency = statistics.mean(latencies)
            stddev_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0.0
        else:
            avg_latency = stddev_latency = 0.0

        # Write latencies and statistics to the output CSV
        with open(output_csv, 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(["latency (ms)", "average latency (ms)", "stddev latency (ms)"])  # Header
            for latency in latencies:
                writer.writerow([latency, avg_latency, stddev_latency])

        print(f"Latencies, average and standard deviation have been written to {output_csv}")

    # Input and output CSV files
    # Input and output CSV files
    input_csv = log_directory.joinpath('latency_log.csv')
    output_csv = log_directory.joinpath('latencies_with_stats.csv')

    # Calculate latencies and update the CSV
    if pathlib.Path(input_csv).exists():
        calculate_latencies(input_csv, output_csv)
    else:
        print(f"No latency log file found at {input_csv}. Skipping latency calculation.")

    if output_csv.exists():
        df = pd.read_csv(output_csv)

        # Extract the latency column
        latency_df = df['latency (ms)']

        # Create a histogram of the latencies
        plt.figure(figsize=(12, 6))
        plt.hist(latency_df, bins=50, color='blue', edgecolor='black', alpha=0.7)
        plt.title('Latency Distribution Over Multiple Runs')
        plt.xlabel('Latency (ms)')
        plt.ylabel('Frequency')
        plt.grid(True, linestyle='--', alpha=0.5)

        # Save the histogram plot
        histogram_plot_path = log_directory.joinpath('latency_histogram.png')
        plt.savefig(histogram_plot_path)
        plt.close()

        print(f"Latency histogram saved to {histogram_plot_path}")

        # Create a line plot showing latency over time
        plt.figure(figsize=(12, 6))
        plt.plot(latency_df, marker='o', linestyle='-', markersize=2)
        plt.title('Latency Over Multiple Runs')
        plt.xlabel('Sample Number')
        plt.ylabel('Latency (ms)')
        plt.grid(True, linestyle='--', alpha=0.5)

        # Save the line plot
        line_plot_path = 'latency_line_plot.png'
        plt.savefig(line_plot_path)
        plt.close()

        print(f"Latency line plot saved to {line_plot_path}")
    else:
        print(f"No latency data available at {output_csv}. Skipping plotting.")
