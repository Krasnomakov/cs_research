#!/usr/bin/env python3
import subprocess

def run_hackrf_sweep_filtered(start_freq_mhz=298, stop_freq_mhz=299, gain_lna=40, gain_vga=20, sweep_count=1):
    cmd = [
        "hackrf_sweep",
        "-f", f"{start_freq_mhz}:{stop_freq_mhz}",
        "-l", str(gain_lna),
        "-g", str(gain_vga),
        "-1",                  # One-shot mode
        "-N", str(sweep_count)
    ]

    try:
        print(f"Running: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        for line in process.stdout:
            if not line or line.startswith("#") or "RAW LINE:" in line:
                continue

            line = line.strip()
            if line.startswith("202"):  # Output line with sweep data
                parts = line.split(",")
                freq_start = int(parts[2])
                freq_end = int(parts[3])

                # Only process bins that fall in desired range
                if 298_000_000 <= freq_start < 299_000_000:
                    db_vals = list(map(float, parts[6:]))
                    print(f"Sweep {freq_start//1_000_000}-{freq_end//1_000_000} MHz → Power(dB): {db_vals}")
        process.wait()

    except KeyboardInterrupt:
        print("Stopped.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_hackrf_sweep_filtered()
