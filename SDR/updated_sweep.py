import matplotlib.pyplot as plt
import pandas as pd
import time
import signal
import sys

# Filepath for the sweep output CSV
csv_file = 'sweep_output.csv'

# Limit how many raw CSV lines we keep each iteration
LINES_TO_PLOT = 2000  # Adjust as needed

# This DataFrame will accumulate maximum power for each frequency bin
peak_data = pd.DataFrame(columns=['Freq_MHz', 'Power_dBm'])

# Handle termination signals (Ctrl+C or termination)
def handle_exit(signum, frame):
    print("\nStopping real-time plotting and cleaning up...")
    plt.close('all')  # Close all Matplotlib windows
    sys.exit(0)

# Register the signal handler
signal.signal(signal.SIGINT, handle_exit)  # Handle Ctrl+C
signal.signal(signal.SIGTERM, handle_exit)  # Handle termination

# Plotting function to handle dynamic updates
def update_plot(live_data, peak_data):
    plt.clf()  # Clear the previous plot

    # Plot the latest "live" sweep
    plt.plot(live_data['Freq_MHz'],
             live_data['Power_dBm'],
             marker='.',
             linestyle='-',
             linewidth=0.7,
             markersize=2,
             color='C0',
             label='Live Sweep')

    # Plot the accumulated "peak hold" sweep
    plt.plot(peak_data['Freq_MHz'],
             peak_data['Power_dBm'],
             marker='.',
             linestyle='-',
             linewidth=0.7,
             markersize=2,
             color='red',
             label='Peak Hold')

    plt.title('Frequency Sweep (HackRF One)', fontsize=14)
    plt.xlabel('Frequency (MHz)', fontsize=12)
    plt.ylabel('Power (dBm)', fontsize=12)
    plt.grid(alpha=0.3)
    plt.legend(loc='best')
    plt.tight_layout()
    plt.savefig('sweep_plot_live.png')  # Save updated plot as an image
    plt.pause(1)  # Pause to allow for the plot to update

# Real-time data processing and plotting
try:
    plt.ion()  # Enable interactive mode so we don't open new windows continuously
    fig = plt.figure()  # Create a persistent figure to reuse

    while True:
        # Load the latest data from the CSV
        new_data = pd.read_csv(
            csv_file,
            sep=',',
            header=None,
            names=[
                'Timestamp', 'Start_Freq', 'Stop_Freq', 'Bin_Width',
                'Gain', 'Bin1', 'Bin2', 'Bin3', 'Bin4', 'Bin5'
            ]
        )

        # Optionally keep only the last N lines for clarity
        if len(new_data) > LINES_TO_PLOT:
            new_data = new_data.tail(LINES_TO_PLOT)

        # Convert necessary columns to numeric
        new_data['Start_Freq'] = pd.to_numeric(new_data['Start_Freq'], errors='coerce')
        new_data['Bin_Width'] = pd.to_numeric(new_data['Bin_Width'], errors='coerce')
        for i in range(1, 6):  # Convert all power bins (Bin1 to Bin5)
            new_data[f'Bin{i}'] = pd.to_numeric(new_data[f'Bin{i}'], errors='coerce')

        # Drop rows with NaN values
        new_data = new_data.dropna()

        # Process the new data into frequency-power pairs for plotting
        bins_data = []
        num_bins = 5  # Number of power bins per row
        for _, row in new_data.iterrows():
            start_freq = row['Start_Freq']
            bin_width = row['Bin_Width']
            timestamp = row['Timestamp']
            for i in range(1, num_bins + 1):
                freq = start_freq + (i - 0.5) * bin_width  # Center frequency for each bin
                power = row[f'Bin{i}']
                bins_data.append((freq / 1e6, power, timestamp))  # convert freq to MHz

        # Turn bins_data into a DataFrame
        df_bins = pd.DataFrame(bins_data, columns=['Freq_MHz', 'Power_dBm', 'Timestamp'])

        # --- LIVE SWEEP ---
        # We'll group by frequency and take the row with the latest timestamp for each frequency
        live_data = df_bins.loc[df_bins.groupby('Freq_MHz')['Timestamp'].idxmax()].copy()

        # --- PEAK HOLD ---
        # We accumulate peak hold across *all time* by merging with the global peak_data
        # 1) Combine new data with existing peak_data
        combined = pd.concat([
            peak_data[['Freq_MHz', 'Power_dBm']],  # old peak hold
            df_bins[['Freq_MHz', 'Power_dBm']]     # new data
        ], ignore_index=True)

        # 2) Group by frequency and take the maximum power
        peak_data = combined.groupby('Freq_MHz', as_index=False)['Power_dBm'].max()

        # Update the plot (live_data vs. peak_data)
        update_plot(live_data, peak_data)

        # Sleep a bit before checking for new data
        time.sleep(2)

except Exception as e:
    print(f"An error occurred: {e}")
    handle_exit(None, None)
