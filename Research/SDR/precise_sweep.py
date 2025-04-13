import matplotlib.pyplot as plt
import pandas as pd
import time
import signal
import sys

# Filepath for the sweep output CSV
csv_file = 'sweep_output.csv'

# Initialize an empty DataFrame to store cumulative data
cumulative_data = pd.DataFrame(columns=['Freq_MHz', 'Power_dBm'])

# Handle termination signals (Ctrl+C or termination)
def handle_exit(signum, frame):
    print("\nStopping real-time plotting and cleaning up...")
    plt.close('all')  # Close all Matplotlib windows
    sys.exit(0)

# Register the signal handler
signal.signal(signal.SIGINT, handle_exit)  # Handle Ctrl+C
signal.signal(signal.SIGTERM, handle_exit)  # Handle termination

# Plotting function to handle dynamic updates
def update_plot(data):
    plt.clf()  # Clear the previous plot
    plt.plot(data['Freq_MHz'], data['Power_dBm'], marker='.', linestyle='-', linewidth=0.5, markersize=1)
    plt.title('Frequency Sweep (HackRF One)', fontsize=14)
    plt.xlabel('Frequency (MHz)', fontsize=12)
    plt.ylabel('Power (dBm)', fontsize=12)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('sweep_plot_live.png')  # Save updated plot as an image
    plt.pause(1)  # Pause to allow for the plot to update

# Real-time data processing and plotting
try:
    plt.ion()  # Enable interactive mode to avoid opening new windows
    fig = plt.figure()  # Create a persistent figure to reuse

    while True:
        # Load the latest data from the CSV
        new_data = pd.read_csv(csv_file, sep=',', header=None, 
                               names=['Timestamp', 'Start_Freq', 'Stop_Freq', 'Bin_Width', 
                                      'Gain', 'Bin1', 'Bin2', 'Bin3', 'Bin4', 'Bin5'])

        # Convert necessary columns to numeric
        new_data['Start_Freq'] = pd.to_numeric(new_data['Start_Freq'], errors='coerce')
        new_data['Bin_Width'] = pd.to_numeric(new_data['Bin_Width'], errors='coerce')
        for i in range(1, 6):  # Convert all power bins (Bin1 to Bin5)
            new_data[f'Bin{i}'] = pd.to_numeric(new_data[f'Bin{i}'], errors='coerce')

        # Drop rows with NaN values
        new_data = new_data.dropna()

        # Process the new data into frequency-power pairs
        bins_data = []
        num_bins = 5  # Number of power bins per row
        for _, row in new_data.iterrows():
            start_freq = row['Start_Freq']
            bin_width = row['Bin_Width']
            for i in range(1, num_bins + 1):
                freq = start_freq + (i - 0.5) * bin_width  # Center frequency for each bin
                power = row[f'Bin{i}']
                bins_data.append((freq / 1e6, power))  # Convert frequency to MHz

        # Convert bins_data into a DataFrame
        new_plot_data = pd.DataFrame(bins_data, columns=['Freq_MHz', 'Power_dBm'])

        # Append new data to the cumulative dataset
        cumulative_data = pd.concat([cumulative_data, new_plot_data]).drop_duplicates()

        # Update the plot with cumulative data
        update_plot(cumulative_data)

        # Wait a bit before checking for new data (adjust as needed)
        time.sleep(2)

except Exception as e:
    print(f"An error occurred: {e}")
    handle_exit(None, None)
