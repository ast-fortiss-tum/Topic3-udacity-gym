import pandas as pd
import matplotlib.pyplot as plt


csv_file_1 = "newv/cpu_usage_log.csv"  # new v - log
csv_file_2 = "oldv/cpu_usage_log.csv"  # old v - log
output_plot_path = 'plot-cpu.png'

df1 = pd.read_csv(csv_file_1)
df2 = pd.read_csv(csv_file_2)




    df1["Timestamp (s)"] = range(len(df1))
    df2["Timestamp (s)"] = range(len(df2))


    df1["CPU Usage (%)"] = pd.to_numeric(df1["CPU Usage (%)"], errors='coerce')
    df2["CPU Usage (%)"] = pd.to_numeric(df2["CPU Usage (%)"], errors='coerce')

    df1.dropna(inplace=True)
    df2.dropna(inplace=True)

    # average CPU usage
    average_cpu_1 = df1["CPU Usage (%)"].mean()
    average_cpu_2 = df2["CPU Usage (%)"].mean()


    print(f"Average CPU Usage (tcp): {average_cpu_1:.2f}%")
    print(f"Average CPU Usage (socket-io): {average_cpu_2:.2f}%")

    # plot CPU usage
    plt.figure(figsize=(10, 5))
    plt.plot(df1["Timestamp (s)"], df1["CPU Usage (%)"], linestyle="dashed", label="tcp")
    plt.plot(df2["Timestamp (s)"], df2["CPU Usage (%)"], linestyle="solid", label="socket-io")

    plt.xlabel("Time (seconds)")
    plt.ylabel("CPU Usage (%)")
    plt.title("CPU Usage Comparison")
    plt.legend()
    plt.grid(True)

    # save it to png
    plt.savefig(output_plot_path, dpi=300)
    print(f"Plot saved successfully as {output_plot_path}")