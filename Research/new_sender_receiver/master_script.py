#!/usr/bin/env python3
"""
master_script.py

1. SSH to a Raspberry Pi to start a CPU load script (sender).
2. On the local machine (receiver), capture HackRF data via SoapySDR.
3. Stop the CPU load script on the Pi.
4. Optionally analyze or plot.

Requires:
  - paramiko (pip install paramiko)
  - SoapySDR, HackRF on local machine
"""

import paramiko
import time
import numpy as np
import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants

###################### CONFIG ######################
PI_HOST = "100.78.212.47"      # Pi IP or hostname
PI_USERNAME = "hdmiadapter"
PI_PASSWORD = "1234"     # or None if using key-based auth
REMOTE_LOAD_SCRIPT = "python3 /home/hdmiadapter/Documents/cs_research/new_sender_receiver/cpu_load.py"

# SDR capture settings
FREQ_HZ = 20e6         # 20 MHz (example)
SAMPLE_RATE = 2e6      # 2 MSPS
GAIN = 40
CAPTURE_SECS = 5.0     # how many seconds to capture
OUTPUT_FILE = "capture_20mhz.iq"
####################################################

def ssh_connect(host, user, password=None, keyfile=None):
    """
    Create and return an SSH client connected to 'host' as 'user'.
    password or keyfile can be used for auth.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if keyfile:
        # key-based auth
        key = paramiko.RSAKey.from_private_key_file(keyfile)
        client.connect(hostname=host, username=user, pkey=key)
    else:
        # password-based
        client.connect(hostname=host, username=user, password=password)
    return client

def ssh_run_bg(client, cmd):
    """
    Run a command in the background on the remote host.
    We'll not wait for completion (like 'nohup cmd &').
    """
    # We can do a trick to run in background with nohup + &
    bg_cmd = f"nohup {cmd} > /dev/null 2>&1 &"
    stdin, stdout, stderr = client.exec_command(bg_cmd)

def ssh_run_block(client, cmd):
    """
    Run a command on the remote host, wait for it to complete, return output.
    """
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    return out, err

def hackrf_capture(freq_hz, sample_rate, gain, duration, outfile):
    """
    Capture 'duration' seconds of IQ data from HackRF via SoapySDR,
    store interleaved float32 (I,Q,I,Q,...) to 'outfile'.
    """
    print(f"Starting HackRF capture at {freq_hz/1e6:.3f} MHz, {sample_rate/1e6:.1f} MSPS, for {duration} s")

    # Setup device
    sdr = SoapySDR.Device(dict(driver="hackrf"))
    rx_chan = 0
    sdr.setSampleRate(SOAPY_SDR_RX, rx_chan, sample_rate)
    sdr.setFrequency(SOAPY_SDR_RX, rx_chan, freq_hz)
    sdr.setGain(SOAPY_SDR_RX, rx_chan, gain)

    rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [rx_chan])
    sdr.activateStream(rx_stream)

    total_samps = int(duration * sample_rate)
    out_data = np.empty(2 * total_samps, dtype=np.float32)  # Interleaved I/Q
    idx = 0
    chunk_size = 8192

    start_time = time.time()
    while idx < (2 * total_samps):
        buff = np.empty(chunk_size, np.complex64)
        sr = sdr.readStream(rx_stream, [buff], chunk_size)
        if sr.ret > 0:
            n = sr.ret
            needed = (2 * total_samps) - idx
            num_float32 = 2 * n

            used = min(needed, num_float32)
            re = buff[:n].real.astype(np.float32)
            im = buff[:n].imag.astype(np.float32)
            interleaved = np.empty(2*n, dtype=np.float32)
            interleaved[0::2] = re
            interleaved[1::2] = im

            out_data[idx : idx+used] = interleaved[:used]
            idx += used
        else:
            # -1 => error, -2 => overflow, -4 => other, etc.
            time.sleep(0.01)

        if (time.time() - start_time) > (duration + 2):
            print("Capture took too long, stopping.")
            break

    sdr.deactivateStream(rx_stream)
    sdr.closeStream(rx_stream)

    if idx < len(out_data):
        out_data = out_data[:idx]

    print(f"Writing {len(out_data)//2} IQ samples to {outfile}")
    out_data.tofile(outfile)
    print("Capture complete.")

def main():
    # 1) SSH into Pi
    print(f"Connecting to {PI_HOST}...")
    client = ssh_connect(PI_HOST, PI_USERNAME, PI_PASSWORD)

    # 2) Start CPU load script in background
    print("Starting CPU load on Pi in background...")
    ssh_run_bg(client, REMOTE_LOAD_SCRIPT)

    # Let it spin up for a bit
    time.sleep(2)

    # 3) Locally capture from HackRF
    hackrf_capture(FREQ_HZ, SAMPLE_RATE, GAIN, CAPTURE_SECS, OUTPUT_FILE)

    # 4) Kill CPU load script (we can find it by name: cpu_load.py)
    #    or we might rely on load script to run forever & do killall
    print("Stopping CPU load script on Pi...")
    ssh_run_block(client, "pkill -f cpu_load.py")

    # 5) Optionally, run more commands or parse the .iq file
    # For now, we just exit
    client.close()
    print("Done. You can now analyze capture file or run a separate analyzer script.")

if __name__ == "__main__":
    main()
