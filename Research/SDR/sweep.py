import matplotlib.pyplot as plt
import pandas as pd

# Load sweep data from CSV file, explicitly using ',' as the delimiter
data = pd.read_csv('sweep_output.csv', sep=',', header=None, 
                   names=['Timestamp', 'Start_Freq', 'Stop_Freq', 'Bin_Width', 
                          'Gain', 'Bin1', 'Bin2', 'Bin3', 'Bin4', 'Bin5'])

# Debug: Print the first few rows of the raw data
print("Raw Data:")
print(data.head())

# Convert necessary columns to numeric
data['Start_Freq'] = pd.to_numeric(data['Start_Freq'], errors='coerce')
data['Bin_Width'] = pd.to_numeric(data['Bin_Width'], errors='coerce')
for i in range(1, 6):  # Convert all power bins (Bin1 to Bin5)
    data[f'Bin{i}'] = pd.to_numeric(data[f'Bin{i}'], errors='coerce')

# Drop rows with NaN values
data = data.dropna()

# Debug: Print the cleaned data
print("Cleaned Data:")
print(data.head())

# Combine Start_Freq and Bin_Width to compute bin center frequencies
num_bins = 5  # Number of power bins per row
bins_data = []

for _, row in data.iterrows():
    start_freq = row['Start_Freq']
    bin_width = row['Bin_Width']
    for i in range(1, num_bins + 1):
        freq = start_freq + (i - 0.5) * bin_width  # Center frequency for each bin
        power = row[f'Bin{i}']
        bins_data.append((freq / 1e6, power))  # Convert frequency to MHz

# Convert bins_data into a DataFrame
plot_data = pd.DataFrame(bins_data, columns=['Freq_MHz', 'Power_dBm'])

# Debug: Print the processed plot data
print("Processed Plot Data:")
print(plot_data.head())

# Ensure there's valid data to plot
if plot_data.empty:
    print("No data to plot. Check the input CSV and parsing logic.")
else:
    # Plot the data
    plt.figure(figsize=(12, 6))
    plt.plot(plot_data['Freq_MHz'], plot_data['Power_dBm'], marker='o', linestyle='-', markersize=2)
    plt.title('Frequency Sweep (HackRF One)')
    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Power (dBm)')
    plt.grid()
    plt.tight_layout()

    # Save the plot or display
    plt.savefig('sweep_plot_fixed.png')  # Save as image (for remote systems)
    plt.show()
