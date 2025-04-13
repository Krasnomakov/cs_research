#!/usr/bin/env python3
"""
receiver_20mhz.py
Listens at ~20 MHz using HackRF, compares to an idle baseline,
prints '1' if we detect a big power jump (CPU load ON).
"""

import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import numpy as np
import time

###################### CONFIG ######################
CENTER_FREQ = 20e6        # 20 MHz
SAMPLE_RATE = 2e6         # 2 MSPS
FFT_SIZE = 8192           # big FFT for narrower bin
GAIN = 40                 # HackRF gain
SIDE_BINS = 5             # average these bins on each side
IDLE_MEASURE_DURATION = 3.0   # measure idle baseline (seconds)
THRESHOLD_DB_ABOVE_IDLE = 3.0 # if spike > 3 dB above idle => "1"
POLL_INTERVAL = 0.05          # how often we read
####################################################

def measure_diff_db(buff, window):
    """
    Given 'buff' (complex64 IQ), compute:
      diff_db = center_bin_power - average_of_side_bins
    Return diff_db, or None if glitch frame.
    """
    spectrum = np.fft.fftshift(np.fft.fft(buff * window))
    power_db = 20 * np.log10(np.abs(spectrum) + 1e-12)

    center_bin = FFT_SIZE // 2
    center_power = power_db[center_bin]
    if center_power < -100:  # glitch or overload
        return None

    left_side = power_db[center_bin - SIDE_BINS : center_bin]
    right_side = power_db[center_bin+1 : center_bin+1+SIDE_BINS]
    if len(left_side) == 0 or len(right_side) == 0:
        return None

    side_avg = np.mean(np.concatenate([left_side, right_side]))
    return center_power - side_avg

def main():
    # Init HackRF
    sdr = SoapySDR.Device(dict(driver="hackrf"))
    sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
    sdr.setFrequency(SOAPY_SDR_RX, 0, CENTER_FREQ)
    sdr.setGain(SOAPY_SDR_RX, 0, GAIN)

    rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
    sdr.activateStream(rxStream)

    window = np.hanning(FFT_SIZE)

    # ---- Measure idle baseline for a few seconds ----
    print(f"Measuring idle baseline at {CENTER_FREQ/1e6:.3f} MHz for {IDLE_MEASURE_DURATION} s...")
    idle_vals = []
    t0 = time.time()
    while (time.time() - t0) < IDLE_MEASURE_DURATION:
        buff = np.zeros(FFT_SIZE, np.complex64)
        sr = sdr.readStream(rxStream, [buff], FFT_SIZE)
        if sr.ret == FFT_SIZE:
            diff_db = measure_diff_db(buff, window)
            if diff_db is not None:
                idle_vals.append(diff_db)
        time.sleep(POLL_INTERVAL)

    if not idle_vals:
        print("ERROR: No baseline readings collected. Check your HackRF or environment.")
        sdr.deactivateStream(rxStream)
        sdr.closeStream(rxStream)
        return

    idle_baseline = np.median(idle_vals)
    print(f"Idle baseline ~ {idle_baseline:.2f} dB\n")
    print("Now monitoring for power jumps...")

    # ---- Continuous Monitoring ----
    try:
        while True:
            buff = np.zeros(FFT_SIZE, np.complex64)
            sr = sdr.readStream(rxStream, [buff], FFT_SIZE)
            if sr.ret != FFT_SIZE:
                continue

            diff_db = measure_diff_db(buff, window)
            if diff_db is None:
                continue

            delta_db = diff_db - idle_baseline
            is_one = (delta_db >= THRESHOLD_DB_ABOVE_IDLE)

            print(f"[{time.strftime('%H:%M:%S')}] diff={diff_db:.2f} dB  Δ={delta_db:.2f} => {'1' if is_one else '0'}")
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        sdr.deactivateStream(rxStream)
        sdr.closeStream(rxStream)

if __name__ == "__main__":
    main()
