import csv
import statistics
import pandas as pd
import matplotlib.pyplot as plt

def calculate_latencies(input_csv, output_csv):
    latencies = []

    with open(input_csv, 'r') as infile:
        reader = csv.reader(infile)
        next(reader)

        send_event = None
        for row in reader:
            timestamp, event, _ = float(row[0]), row[1], row[2]

            if event == 'send':
                send_event = timestamp
            elif event == 'receive' and send_event is not None:
                latency = (timestamp - send_event) * 1000
                latencies.append(latency)
                send_event = None

    if latencies:
        avg_latency = statistics.mean(latencies)
        stddev_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0.0
    else:
        avg_latency = stddev_latency = 0.0

    with open(output_csv, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["latency (ms)", "average latency (ms)", "stddev latency (ms)"])
        for latency in latencies:
            writer.writerow([latency, avg_latency, stddev_latency])

    print(f"Latencies, average and standard deviation have been written to {output_csv}")



# old version latencies
input_csv = 'oldv/latency_oldV.csv'
output_csv = 'latencies_old.csv'

calculate_latencies(input_csv, output_csv)

# new version latencies
input_csv = 'newv/latency_newV.csv'
output_csv = 'latencies_new.csv'

calculate_latencies(input_csv, output_csv)








df1 = pd.read_csv('latencies_old.csv')
df2 = pd.read_csv('latencies_new.csv')

latency_df1 = df1['latency (ms)']
latency_df2 = df2['latency (ms)']


plt.figure(figsize=(10, 6))
plt.boxplot([latency_df1, latency_df2], tick_labels=['SocketIO', 'TCP Connection'], patch_artist=True)


plt.title('Latency Comparison Between SocketIO and TCP Connectionnn')
plt.ylabel('Latency (ms)')
plt.grid(True, linestyle='--', alpha=0.5)


plt.savefig('latency_comparison.png')

