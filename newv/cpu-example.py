import json
import pathlib
import time
import tqdm
import psutil
import csv
from udacity_gym import UdacitySimulator, UdacityGym, UdacityAction
from udacity_gym.agent import PIDUdacityAgent
from udacity_gym.agent_callback import LogObservationCallback

if __name__ == '__main__':

    # Configuration settings
    host = "127.0.0.1"
    port = 4567
    simulator_exe_path = "Linux Build/Linux Build.x86_64"
    assert pathlib.Path(simulator_exe_path).exists(), f"Simulator binary not found at {simulator_exe_path}"

    # Track settings
    track = "lake"
    daytime = "day"
    weather = "sunny"
    log_directory = pathlib.Path(f"udacity_dataset_lake_12_12_2/{track}_{weather}_{daytime}")

    # Path for log file
    cpu_log_file = "cpu_usage_log.csv"

    # Creating the simulator wrapper
    simulator = UdacitySimulator(
        sim_exe_path=simulator_exe_path,
        host=host,
        port=port,
    )

    # Creating the gym environment
    env = UdacityGym(simulator=simulator)
    simulator.start()
    observation, _ = env.reset(track=f"{track}", weather=f"{weather}", daytime=f"{daytime}")

    # Wait for environment to set up
    while not observation or not observation.is_ready():
        observation = env.observe()
        print("Waiting for environment to set up...")
        time.sleep(1)

    log_observation_callback = LogObservationCallback(log_directory)
    agent = PIDUdacityAgent(
        kp=0.05, kd=0.8, ki=0.000001,
        before_action_callbacks=[],
        after_action_callbacks=[log_observation_callback],
    )

    # Open CSV file
    with open(cpu_log_file, mode='w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(["CPU Usage (%)"])  # CSV Header

        cpu_usages = []

        # Interacting with the gym environment
        for _ in tqdm.tqdm(range(60)):
            action = agent(observation)
            last_observation = observation
            observation, reward, terminated, truncated, info = env.step(action)

            cpu_usage = psutil.cpu_percent(interval=1)  # Measure CPU usage
            cpu_usages.append(cpu_usage)

            csv_writer.writerow([cpu_usage])
            print(f"CPU Usage: {cpu_usage}%")

            while observation.time == last_observation.time:
                observation = env.observe()
                time.sleep(0.0025)

    if cpu_usages:
        avg_cpu_usage = sum(cpu_usages) / len(cpu_usages)
        print(f"\nAverage CPU Usage during simulation: {avg_cpu_usage:.2f}%")

    if info:
        json.dump(info, open(log_directory.joinpath("info.json"), "w"))

    log_observation_callback.save()
    simulator.close()
    env.close()
    print(f"Experiment concluded. CPU usage logged in: {cpu_log_file}")
