#!/usr/bin/env python3
"""
master_script.py

1. SSH into Pi, start stronger_sender.py in the foreground.
   - Read each bit event + timestamp from the Pi's stdout.
2. On local PC, run HackRF capture for CAPTURE_SECS using SoapySDR.
3. Log everything:
   - Start/stop times of local capture
   - Bit events from Pi
4. Kill the sender script after capturing.

Requires: paramiko (pip install paramiko), SoapySDR installed locally.
"""

import paramiko
import sys
import time
import numpy as np
import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import threading
import datetime

################### CONFIG ###################
PI_HOST = "your_ip"
PI_USER = "your_user_name"
PI_PASS = "your_password"
REMOTE_SENDER_CMD = "python3 -u /home/your_user_name/Documents/new_sender_receiver/stronger_sender.py"

CAPTURE_SECS = 10.0
OUTPUT_FILE = "capture_20mhz.iq"

FREQ_HZ = 20e6       # 20 MHz
SAMPLE_RATE = 2e6    # 2 MSPS
GAIN = 40
##############################################

def ssh_connect(host, user, password=None):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=user, password=password)
    return client

def local_hackrf_capture(freq_hz, sr, gain, duration, outfile):
    """
    Capture 'duration' seconds from HackRF at freq_hz, sr
    Store interleaved float32 IQ in 'outfile'.
    """
    print(f"[Master] Starting HackRF capture for {duration} s at {freq_hz/1e6:.3f} MHz")
    sdr = SoapySDR.Device(dict(driver="hackrf"))
    rx_chan = 0
    sdr.setSampleRate(SOAPY_SDR_RX, rx_chan, sr)
    sdr.setFrequency(SOAPY_SDR_RX, rx_chan, freq_hz)
    sdr.setGain(SOAPY_SDR_RX, rx_chan, gain)

    rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [rx_chan])
    sdr.activateStream(rx_stream)

    total_samps = int(duration * sr)
    out_data = np.empty(2*total_samps, dtype=np.float32)
    idx = 0
    chunk_size = 8192

    start_t = time.time()
    while idx < (2*total_samps):
        buff = np.empty(chunk_size, np.complex64)
        sr_ret = sdr.readStream(rx_stream, [buff], chunk_size)
        if sr_ret.ret > 0:
            n = sr_ret.ret
            needed = (2*total_samps) - idx
            num_float32 = 2*n
            used = min(needed, num_float32)

            re = buff[:n].real.astype(np.float32)
            im = buff[:n].imag.astype(np.float32)
            interleaved = np.empty(2*n, dtype=np.float32)
            interleaved[0::2] = re
            interleaved[1::2] = im

            out_data[idx: idx+used] = interleaved[:used]
            idx += used
        else:
            time.sleep(0.001)

        if (time.time() - start_t) > (duration + 2):
            print("[Master] Took too long capturing, stopping.")
            break

    sdr.deactivateStream(rx_stream)
    sdr.closeStream(rx_stream)

    # If short
    if idx < len(out_data):
        out_data = out_data[:idx]

    print(f"[Master] Writing {len(out_data)//2} samples to {outfile}")
    out_data.tofile(outfile)
    print("[Master] Capture done.")

def main():
    # 1) SSH connect
    print(f"[Master] Connecting to {PI_HOST}...")
    client = ssh_connect(PI_HOST, PI_USER, PI_PASS)

    # 2) Start stronger_sender.py in foreground
    print("[Master] Starting stronger_sender.py on Pi...")
    transport = client.get_transport()
    chan = transport.open_session()
    # 'exec_command' but we want to read stdout as it runs
    chan.exec_command(REMOTE_SENDER_CMD)

    # We'll read lines from 'chan.makefile' to get bit events
    stdout_file = chan.makefile("r")
    stderr_file = chan.makefile_stderr("r")

    # 3) Thread to read bit events
    bit_events = []
    def reader_thread():
        for line in stdout_file:
            line = line.strip()
            if line.startswith("[TX]"):
                # e.g. "[TX] 13:17:36.123456 BIT=1"
                bit_events.append(line)
            else:
                # Maybe "Transmitting bitstream: 010"
                print(f"[Pi-Log] {line}")

    rt = threading.Thread(target=reader_thread, daemon=True)
    rt.start()

    # Sleep a little so sender starts
    time.sleep(2)
    print("[Master] Starting local HackRF capture...")

    # 4) Do local capture
    local_start_time = datetime.datetime.now()
    local_hackrf_capture(FREQ_HZ, SAMPLE_RATE, GAIN, CAPTURE_SECS, OUTPUT_FILE)
    local_end_time = datetime.datetime.now()

    # 5) Stop the sender script
    print("[Master] Stopping sender script on Pi...")
    # We'll forcibly kill that remote process. 
    # Alternatively, we could send Ctrl+C, but let's do pkill:
    kill_cmd = "pkill -f stronger_sender.py"
    stdin, stdout, stderr = client.exec_command(kill_cmd)
    _ = stdout.read().decode()
    _ = stderr.read().decode()

    # Wait a moment for remote to exit
    time.sleep(1)
    chan.close()
    client.close()

    # 6) Print final logs
    print("\n[Master] Local capture from", local_start_time, "to", local_end_time)
    print("[Master] Received Pi bit events:")
    for evt in bit_events:
        print("   ", evt)

    # You can save these logs to a file or do more analysis next.
    print("[Master] All done.")

if __name__ == "__main__":
    main()
