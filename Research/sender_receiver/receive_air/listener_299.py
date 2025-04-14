#!/usr/bin/env python3
import subprocess
import csv
from datetime import datetime

def run_hackrf_sweep_stream(start_freq_mhz=298, stop_freq_mhz=299, target_freq_mhz=299, gain_lna=40, gain_vga=20):
    """
    Run hackrf_sweep continuously, filter for only the bin that includes 299 MHz, and log power to CSV.
    """
    cmd = [
        "hackrf_sweep",
        "-f", f"{start_freq_mhz}:{stop_freq_mhz}",
        "-l", str(gain_lna),
        "-g", str(gain_vga),
        "-N", "0"  # 0 = stream forever
    ]

    print(f"Running: {' '.join(cmd)}")
    
    output_file = "power_299MHz.csv"
    with open(output_file, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "power_dB"])

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )

                        for line in process.stdout:
                            if not line:
                                continue

                            line = line.strip()
                            # Skip comment lines or malformed output
                            if not line.startswith("2025") or ',' not in line or len(line.split(",")) < 7:
                                continue

                            try:
                                parts = line.split(",")
                                freq_start = int(parts[2])
                                bin_width = float(parts[4])
                                db_values = list(map(float, parts[6:]))

                                max_db = max(db_values)
                                ndb_values = [db - max_db for db in db_values]

                                for i, (db, ndb) in enumerate(zip(db_values, ndb_values)):
                                    bin_freq = freq_start + int(i * bin_width)

                                    if bin_freq <= 299_000_000 < (bin_freq + bin_width):
                                        timestamp = f"{parts[0]} {parts[1]}"
                                        bin_freq_mhz = bin_freq / 1e6
                                        event = "YES" if db > -60 else ""
                                        writer.writerow([timestamp, bin_freq_mhz, db, ndb, event])
                                        print(f"[{timestamp}] {bin_freq_mhz:.3f} MHz → dB: {db:.1f}, nDB: {ndb:.1f} {event}")
                                        break

                            except Exception as parse_err:
                                print(f"⚠️  Skipping line (parse error): {parse_err}")


            process.wait()

        except KeyboardInterrupt:
            print("Stopped by user.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            print(f"\nSaved to: {output_file}")

if __name__ == "__main__":
    run_hackrf_sweep_stream()
