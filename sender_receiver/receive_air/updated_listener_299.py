#!/usr/bin/env python3
import subprocess
import csv

def run_peak_logger(start_freq_mhz=298, stop_freq_mhz=299, target_freq_mhz=299, gain_lna=40, gain_vga=20):
    """
    Continuously run hackrf_sweep in a narrow band, parse only lines with valid sweep data,
    find the bin that contains 'target_freq_mhz', and store timestamp + dB + nDB to CSV.
    Ignores 'total sweeps completed' lines or any lines that don't match expected format.
    """
    cmd = [
        "hackrf_sweep",
        "-f", f"{start_freq_mhz}:{stop_freq_mhz}",
        "-l", str(gain_lna),
        "-g", str(gain_vga),
        "-N", "0"  # stream forever
    ]
    print(f"Running: {' '.join(cmd)}")

    output_file = "power_299MHz_peaks.csv"
    with open(output_file, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # CSV Header
        writer.writerow(["timestamp", "bin_freq_mhz", "power_dB", "power_nDB"])

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )

            for line in process.stdout:
                # Clean the line
                if not line:
                    continue
                line = line.strip()

                # Skip unwanted lines
                # 1) "total sweeps completed"
                if "total sweeps completed" in line:
                    continue
                # 2) lines that obviously don't start with a date/time stamp
                if not line.startswith("202"):
                    continue
                # 3) lines that don't have enough commas to be valid data lines
                parts = line.split(",")
                if len(parts) < 7:
                    continue

                try:
                    freq_start = int(parts[2])
                    bin_width = float(parts[4])
                    db_values = list(map(float, parts[6:]))

                    max_db = max(db_values)
                    ndb_values = [db - max_db for db in db_values]

                    # Find bin containing target_freq_mhz
                    freq_target_hz = int(target_freq_mhz * 1e6)
                    for i, (db, ndb) in enumerate(zip(db_values, ndb_values)):
                        bin_freq_start = freq_start + int(i * bin_width)
                        bin_freq_end = bin_freq_start + bin_width

                        if bin_freq_start <= freq_target_hz < bin_freq_end:
                            timestamp = parts[0] + " " + parts[1]
                            bin_freq_mhz = bin_freq_start / 1e6
                            writer.writerow([timestamp, bin_freq_mhz, db, ndb])
                            # Optional console print
                            print(f"[{timestamp}] {bin_freq_mhz:.3f} MHz → dB: {db:.1f}, nDB: {ndb:.1f}")
                            break

                except Exception as parse_err:
                    # If there's any parsing issue, skip that line but keep going
                    print(f"Skipping line due to parse error: {parse_err}")

            process.wait()

        except KeyboardInterrupt:
            print("\nStopped by user.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            print(f"Saved to: {output_file}")

if __name__ == "__main__":
    run_peak_logger()
