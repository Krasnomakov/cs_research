#!/usr/bin/env python3
import subprocess
import sys
import time
import numpy as np
import matplotlib.pyplot as plt

def main():
    # Adjust bin width as desired: e.g. 100000 = 100 kHz
    BIN_WIDTH = 100000  
    cmd = [
        "hackrf_sweep",
        "-f", "298:301",
        "-l", "40",      # LNA gain
        "-g", "20",      # VGA gain
        "-w", str(BIN_WIDTH),
        "-N", "0"        # 0 = sweep forever
    ]
    print(f"Running: {' '.join(cmd)}")

    # Start hackrf_sweep
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    except FileNotFoundError:
        print("Error: hackrf_sweep not found or not in PATH.")
        sys.exit(1)

    plt.ion()
    fig, ax = plt.subplots()
    ax.set_title("HackRF Sweep 298–301 MHz (Accumulated Plot)")
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel("Power (dB)")
    ax.set_xlim(298, 301)
    ax.set_ylim(-100, 0)

    # We'll accumulate partial lines in a list of (freq_in_mhz, dB)
    spectrum_data = []

    last_plot_time = time.time()

    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break  # hackrf_sweep ended

            line = line.strip()

            # Skip lines that don't contain actual sweep data
            if not line.startswith("202") or "total sweeps completed" in line:
                continue

            parts = line.split(",")
            if len(parts) < 7:
                continue

            # Parse hackrf_sweep data line
            try:
                freq_start = int(parts[2])       # Hz
                freq_end   = int(parts[3])       # Hz
                bin_width  = float(parts[4])     # Hz per bin
                db_values  = list(map(float, parts[6:]))

                # Construct array of bin frequencies
                freqs_hz = np.array([freq_start + i*bin_width for i in range(len(db_values))])
                db_values = np.array(db_values)

                # Filter to [298e6, 301e6]
                keep = (freqs_hz >= 298e6) & (freqs_hz <= 301e6)
                freqs_hz = freqs_hz[keep]
                db_values = db_values[keep]

                # Append to our main buffer
                for f, db in zip(freqs_hz, db_values):
                    # Convert freq to MHz
                    spectrum_data.append((f / 1e6, db))

            except ValueError:
                # Couldn’t parse floats on this line → skip
                continue

            # Once per second, update the plot
            if time.time() - last_plot_time >= 1.0:
                if len(spectrum_data) > 0:
                    # Sort by frequency
                    spectrum_data.sort(key=lambda x: x[0])

                    # Convert to separate arrays for plotting
                    freqs_mhz = [item[0] for item in spectrum_data]
                    powers_db = [item[1] for item in spectrum_data]

                    ax.clear()
                    ax.set_title("HackRF Sweep 298–301 MHz (Accumulated Plot)")
                    ax.set_xlabel("Frequency (MHz)")
                    ax.set_ylabel("Power (dB)")
                    ax.set_xlim(298, 301)
                    ax.set_ylim(-100, 0)
                    ax.plot(freqs_mhz, powers_db)

                    plt.pause(0.01)

                    # Clear the buffer so next second we show fresh data
                    spectrum_data.clear()

                last_plot_time = time.time()

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        print("Terminating hackrf_sweep...")
        process.terminate()
        process.wait()


if __name__ == "__main__":
    main()
