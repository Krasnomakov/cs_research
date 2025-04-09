#!/usr/bin/env python3
"""
master_plus_analyzer.py

1) SSH into a Pi, run stronger_sender.py in foreground (unbuffered),
   collecting lines like "[TX] HH:MM:SS.ssssss BIT=1".
2) Locally capture HackRF data to 'capture_18mhz.iq'
   for CAPTURE_SECS seconds.
3) Kill sender on Pi.
4) Perform short-time FFT on the .iq file to see amplitude vs. time
   near center freq. Overlay vertical lines for bit events.

Requires:
  - paramiko (SSH)
  - SoapySDR (for HackRF)
  - matplotlib + numpy
"""

import paramiko
import threading
import time
import datetime
import numpy as np
import matplotlib.pyplot as plt
import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants

######################## CONFIG ########################
PI_HOST = "100.78.212.47"
PI_USER = "hdmiadapter"
PI_PASS = "1234"
REMOTE_SENDER_CMD = "python3 -u /home/hdmiadapter/Documents/new_sender_receiver/stronger_sender.py"

CAPTURE_SECS = 10.0
OUTPUT_IQ_FILE = "capture_18mhz.iq"
FREQ_HZ = 18e6
SAMPLE_RATE = 2e6
GAIN = 40

FRAME_SIZE = 4096
HOP_SIZE = 2048
CENTER_BIN_WIDTH = 2

# If your Pi & local PC clocks differ by some seconds,
# you can shift Pi event times by TIME_OFFSET_GUESS to align
# them with local capture t=0. E.g., 2.0 if the Pi is 2s behind.
TIME_OFFSET_GUESS = 0.0
########################################################

def ssh_connect(host, user, password=None):
    """Open a paramiko SSHClient to the Pi."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=user, password=password)
    return client

def hackrf_capture(freq_hz, sr, gain, duration, outfile):
    """
    Capture 'duration' seconds of IQ data from HackRF to 'outfile' (float32 interleaved).
    """
    print(f"[Master] Starting HackRF capture for {duration:.1f} s "
          f"at {freq_hz/1e6:.3f} MHz, SR={sr/1e6:.1f} MSPS")
    sdr = SoapySDR.Device(dict(driver="hackrf"))
    rx_chan = 0
    sdr.setSampleRate(SOAPY_SDR_RX, rx_chan, sr)
    sdr.setFrequency(SOAPY_SDR_RX, rx_chan, freq_hz)
    sdr.setGain(SOAPY_SDR_RX, rx_chan, gain)

    rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [rx_chan])
    sdr.activateStream(rx_stream)

    total_samps = int(duration * sr)
    out_data = np.empty(2 * total_samps, dtype=np.float32)
    idx = 0
    chunk_size = 8192

    start_t = time.time()
    while idx < (2 * total_samps):
        buff = np.empty(chunk_size, np.complex64)
        sr_ret = sdr.readStream(rx_stream, [buff], chunk_size)
        if sr_ret.ret > 0:
            n = sr_ret.ret
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
            time.sleep(0.001)

        if (time.time() - start_t) > (duration + 2.0):
            print("[Master] Timeout capturing, stopping early.")
            break

    sdr.deactivateStream(rx_stream)
    sdr.closeStream(rx_stream)

    if idx < len(out_data):
        out_data = out_data[:idx]

    print(f"[Master] Storing {len(out_data)//2} IQ samples to {outfile}")
    out_data.tofile(outfile)
    print("[Master] Capture complete.\n")

def parse_pi_bit_line(line):
    """
    Parse a line like: "[TX] 13:17:36.123456 BIT=1"
    Returns (datetime_object, bit_str) or None if invalid.
    """
    parts = line.strip().split()
    if len(parts) < 3:
        return None
    # e.g. parts[0]="[TX]", parts[1]="13:17:36.123456", parts[2]="BIT=1"
    time_str = parts[1]              # "13:17:36.123456"
    bit_str = parts[2].split("=")[1] # "1"

    try:
        dt_today = datetime.datetime.combine(
            datetime.date.today(),
            datetime.datetime.strptime(time_str, "%H:%M:%S.%f").time()
        )
        return (dt_today, bit_str)
    except ValueError:
        return None

def short_time_fft_analysis(iq_file, sample_rate, frame_size, hop_size, center_bw):
    """
    Compute short-time FFT from 'iq_file' (float32 interleaved),
    return list of (time_sec, amplitude_dB).
    """
    raw = np.fromfile(iq_file, dtype=np.float32)
    if len(raw) < 2:
        print(f"[Analysis] IQ file {iq_file} too small or missing.")
        return []

    iq = raw.view(np.complex64)
    num_samps = iq.size
    duration_sec = num_samps / sample_rate
    print(f"[Analysis] Loaded {num_samps} samples -> ~{duration_sec:.2f} s of data.")

    window = np.hanning(frame_size)
    idx = 0
    result = []
    frame_count = 0

    while (idx + frame_size) <= num_samps:
        segment = iq[idx : idx + frame_size]
        spectrum = np.fft.fftshift(np.fft.fft(segment * window))
        mag_db = 20 * np.log10(np.abs(spectrum) + 1e-12)

        center_bin = frame_size // 2
        band_slice = mag_db[center_bin - center_bw : center_bin + center_bw +1]
        band_mean = np.mean(band_slice)

        # time for middle of the frame
        mid_sample = idx + (frame_size/2)
        t_sec = mid_sample / sample_rate

        result.append((t_sec, band_mean))
        idx += hop_size
        frame_count += 1

    print(f"[Analysis] Created {frame_count} frames, each ~{frame_size/sample_rate*1e3:.1f} ms.")
    return result

def main():
    # 1) SSH connect
    print(f"[Master] Connecting to {PI_HOST}...")
    client = ssh_connect(PI_HOST, PI_USER, PI_PASS)

    # 2) Start stronger_sender.py in foreground
    print("[Master] Starting stronger_sender.py on Pi (foreground)...")
    transport = client.get_transport()
    chan = transport.open_session()

    # run unbuffered so we get immediate lines
    chan.exec_command(REMOTE_SENDER_CMD)
    stdout_file = chan.makefile("r")
    stderr_file = chan.makefile_stderr("r")

    # 3) read lines from Pi in a thread
    bit_events = []
    def reader_thread():
        for line in stdout_file:
            line = line.strip()
            if line.startswith("[TX]"):
                parsed = parse_pi_bit_line(line)
                if parsed:
                    dt_obj, bit_val = parsed
                    bit_events.append((dt_obj, bit_val))
            else:
                print(f"[Pi-Log] {line}")

    rt = threading.Thread(target=reader_thread, daemon=True)
    rt.start()

    # Let the sender start for a bit
    time.sleep(2)

    # 4) Local HackRF capture
    local_start_dt = datetime.datetime.now()
    hackrf_capture(FREQ_HZ, SAMPLE_RATE, GAIN, CAPTURE_SECS, OUTPUT_IQ_FILE)
    local_end_dt = datetime.datetime.now()

    # 5) Kill sender
    print("[Master] Stopping stronger_sender.py on Pi...")
    kill_cmd = "pkill -f stronger_sender.py"
    client.exec_command(kill_cmd)
    time.sleep(1)
    chan.close()
    client.close()

    # 6) Short-time FFT
    print("[Master] Starting analysis of captured IQ data...")
    stft_result = short_time_fft_analysis(
        OUTPUT_IQ_FILE,
        SAMPLE_RATE,
        FRAME_SIZE,
        HOP_SIZE,
        CENTER_BIN_WIDTH
    )
    times_sec = [r[0] for r in stft_result]
    amps_db   = [r[1] for r in stft_result]

    # 7) time offset function
    def pi_dt_to_local_seconds(pi_dt: datetime.datetime) -> float:
        delta = (pi_dt - local_start_dt).total_seconds()
        return delta + TIME_OFFSET_GUESS

    # 8) plot amplitude vs. time, overlay bit events
    plt.figure()
    plt.plot(times_sec, amps_db, label="Amplitude (dB @ center)")
    for (dt_obj, bit_val) in bit_events:
        sec_local = pi_dt_to_local_seconds(dt_obj)
        # show vertical lines if in capture range
        if 0 <= sec_local <= (times_sec[-1] + 0.5):
            plt.axvline(x=sec_local, linestyle='--')
            plt.text(sec_local+0.01, max(amps_db), f"BIT={bit_val}", rotation=90)

    plt.xlabel("Time (seconds from start of local capture)")
    plt.ylabel("Amplitude (dB)")
    plt.title("Short-Time FFT vs. Pi Bits (Merged View)")
    plt.grid(True)
    plt.legend()

    # 9) log final results
    print("\n[Master] Local capture started at", local_start_dt, "and ended at", local_end_dt)
    print("[Master] Pi bit events (with local offset applied):")
    for (dt_obj, bit_val) in bit_events:
        sec_local = pi_dt_to_local_seconds(dt_obj)
        print(f"   PiTime={dt_obj.time()} => localSec={sec_local:.3f} => BIT={bit_val}")

    plt.show()
    print("[Master] Done.")

if __name__ == "__main__":
    main()
