#!/usr/bin/env python3
"""
analyze_capture.py

Loads 'capture_20mhz.iq' (interleaved float32 I/Q),
computes short-time FFT frames, extracts the amplitude
near the center frequency, and plots amplitude vs. time.

You can then overlay or compare with sender bit events
to see how the amplitude changes for "1" vs. "0".
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import datetime

################## CONFIG ##################
IQ_FILE = "capture_20mhz.iq"
SAMPLE_RATE = 2e6   # 2 MSPS, must match the recording
FRAME_SIZE = 4096   # FFT size for short-time frames
HOP_SIZE = 2048     # overlap or skip between frames
CENTER_BIN_WIDTH = 2   # how many bins to average around center
################## CONFIG ##################

def main():
    # 1) Load the entire IQ file (float32 interleaved I/Q).
    print(f"Loading {IQ_FILE}...")
    raw = np.fromfile(IQ_FILE, dtype=np.float32)
    if len(raw) < 2:
        print("File is too small or missing.")
        sys.exit(1)

    # Convert to complex64 array.
    # raw[0::2] => I, raw[1::2] => Q
    iq = raw.view(np.complex64)
    num_samples = iq.size
    print(f"Loaded {num_samples} IQ samples. Duration ~ {num_samples / SAMPLE_RATE:.3f}s")

    # 2) Compute short-time FFT frames
    # We'll do: frame #0 => iq[0:FRAME_SIZE]
    #           frame #1 => iq[HOP_SIZE : HOP_SIZE+FRAME_SIZE]
    # etc. until we run out of samples.
    window = np.hanning(FRAME_SIZE)
    frames_amp = []   # store (time_seconds, amplitude_dB)

    idx = 0
    frame_count = 0

    while (idx + FRAME_SIZE) <= num_samples:
        segment = iq[idx : idx + FRAME_SIZE]
        # Window + FFT
        spectrum = np.fft.fftshift(np.fft.fft(segment * window))
        mag_db = 20 * np.log10(np.abs(spectrum) + 1e-12)

        # The center bin is at FRAME_SIZE//2 in the shifted spectrum
        center_bin = FRAME_SIZE // 2
        # We'll average a few bins around center
        half_bw = CENTER_BIN_WIDTH
        band_slice = mag_db[center_bin - half_bw : center_bin + half_bw+1]
        band_mean = np.mean(band_slice)

        # Approx time offset in seconds from start of capture
        # We pick the midpoint of the frame => idx + FRAME_SIZE/2
        mid_sample = idx + (FRAME_SIZE / 2.0)
        t_sec = mid_sample / SAMPLE_RATE

        frames_amp.append((t_sec, band_mean))
        frame_count += 1
        idx += HOP_SIZE

    print(f"Computed {frame_count} frames, each ~ {FRAME_SIZE/SAMPLE_RATE*1e3:.1f} ms long")

    # 3) Plot amplitude vs. time
    times = [x[0] for x in frames_amp]
    amps_db = [x[1] for x in frames_amp]

    plt.figure()
    plt.plot(times, amps_db, label="Center amplitude (dB)")
    plt.xlabel("Time (seconds from start of capture)")
    plt.ylabel("Amplitude (dB)")
    plt.title("Short-Time FFT: CPU Load vs. Amplitude @ ~20 MHz")
    plt.grid(True)
    plt.legend()

    # 4) Optionally, overlay sender bit events
    # If you have a file with lines like:
    #   "[TX] 13:17:36.123456 BIT=1"
    # you can parse + approximate alignment.
    BIT_LOG_FILE = "bit_events.log"  # or whatever
    try:
        bit_events = load_bit_log(BIT_LOG_FILE)
        # We don't have perfect sync, but we can e.g. place them on this plot
        # by guessing a start offset. If you know the approximate offset between
        # Pi time + local capture start time, set it here:
        local_capture_start = 0.0  # second 0 in your chart
        offset_guess = 2.0        # e.g. we guess we started 2s after the Pi.

        for (timestamp_str, bit_char) in bit_events:
            # We won't do perfect parse of HH:MM:SS.ms. We'll just place a text
            # label or vertical line near offset_guess + some delta
            # Just an example approach:
            # parse "13:17:36.123456"
            # convert to seconds-of-day or some reference
            # then subtract sender start time, etc.
            pass
    except FileNotFoundError:
        print("No bit event file found or skipping overlay. You can implement alignment here.")

    plt.show()

def load_bit_log(path):
    """
    Example parser for lines like:
      "[TX] 13:17:36.123456 BIT=1"
    Return list of (timestamp_str, bit_char).
    """
    events = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[TX]"):
                # e.g. "[TX] 13:17:36.123456 BIT=1"
                # split by space => ["[TX]", "13:17:36.123456", "BIT=1"]
                parts = line.split()
                ts_str = parts[1]  # "13:17:36.123456"
                bit_str = parts[2] # "BIT=1"
                bit_val = bit_str.split("=")[1]
                events.append((ts_str, bit_val))
    return events

if __name__ == "__main__":
    main()
