#!/usr/bin/env python3
"""
band_scanner.py

Loops over a range of frequencies (e.g. 200–300 MHz in steps of 10 MHz),
performs a short capture at each frequency using HackRF (SoapySDR),
computes the average amplitude near the center bin (short-time FFT),
and prints the result.

Usage:
  1) Edit START_FREQ, STOP_FREQ, STEP_FREQ as desired.
  2) Run once when Pi is idle.
  3) Run again when Pi is under CPU load.
  4) Compare the two sets of amplitude readings.

Press Ctrl+C to stop early if needed.
"""

import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import numpy as np
import time

################## CONFIG ##################
START_FREQ = 200e6   # e.g. 200 MHz
STOP_FREQ  = 300e6   # e.g. 300 MHz
STEP_FREQ  = 1e6    # e.g. 10 MHz increments

SAMPLE_RATE = 2e6
GAIN = 40

FFT_SIZE = 4096
CENTER_BIN_WIDTH = 1   # how many bins around center to average
CAPTURE_TIME_SEC = 1.0 # how many seconds per frequency

################## CONFIG ##################

def main():
    # 1) Open the HackRF device
    print("[INFO] Initializing HackRF via SoapySDR...")
    sdr = SoapySDR.Device(dict(driver="hackrf"))
    rx_chan = 0
    sdr.setSampleRate(SOAPY_SDR_RX, rx_chan, SAMPLE_RATE)
    sdr.setGain(SOAPY_SDR_RX, rx_chan, GAIN)

    rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [rx_chan])
    sdr.activateStream(rxStream)

    # Window for FFT
    window = np.hanning(FFT_SIZE)
    chunk_size = FFT_SIZE

    # 2) Iterate over frequencies
    freqs = []
    f = START_FREQ
    while f <= STOP_FREQ + 1:  # +1 to ensure float rounding doesn’t skip stop
        freqs.append(f)
        f += STEP_FREQ

    print(f"[INFO] Will scan {len(freqs)} freqs from {START_FREQ/1e6:.1f} to {STOP_FREQ/1e6:.1f} MHz")

    results = []

    for freq in freqs:
        print(f"\n[SCAN] Tuning to {freq/1e6:.3f} MHz ...")
        sdr.setFrequency(SOAPY_SDR_RX, rx_chan, freq)

        # We'll collect data for CAPTURE_TIME_SEC, measure amplitude in the center bin
        start_t = time.time()
        center_amps = []
        while (time.time() - start_t) < CAPTURE_TIME_SEC:
            buff = np.empty(chunk_size, np.complex64)
            sr = sdr.readStream(rxStream, [buff], chunk_size)
            if sr.ret == chunk_size:
                spectrum = np.fft.fftshift(np.fft.fft(buff * window))
                mag_db = 20 * np.log10(np.abs(spectrum) + 1e-12)
                center_bin = FFT_SIZE // 2
                band_slice = mag_db[center_bin - CENTER_BIN_WIDTH : center_bin + CENTER_BIN_WIDTH + 1]
                avg_power = np.mean(band_slice)
                center_amps.append(avg_power)
            else:
                # partial read or error => small sleep
                time.sleep(0.001)

        if center_amps:
            freq_avg_db = np.mean(center_amps)
        else:
            freq_avg_db = float('nan')

        print(f"[SCAN] {freq/1e6:.1f} MHz => avg amplitude ~ {freq_avg_db:.2f} dB")
        results.append((freq, freq_avg_db))

    # 3) Cleanup
    sdr.deactivateStream(rxStream)
    sdr.closeStream(rxStream)

    print("\n[RESULTS] Summary of average amplitude per frequency:")
    for (freq, db) in results:
        print(f"  {freq/1e6:.1f} MHz => {db:.2f} dB")

    print("\n[INFO] Done scanning.")

if __name__ == "__main__":
    main()
