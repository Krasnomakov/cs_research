#!/usr/bin/env python3
import SoapySDR
from SoapySDR import *
import numpy as np
import time

###################### CONFIG ######################
CENTER_FREQ = 299.8e6     # match the GQRX peak freq
SAMPLE_RATE = 2e6         # small focus
FFT_SIZE = 8192           # bigger FFT for narrow spike
GAIN = 40
SIDE_BINS = 5             # how many bins to average each side
WINDOW = np.hanning(FFT_SIZE)

IDLE_MEASURE_DURATION = 3.0    # seconds measuring idle baseline
THRESHOLD_DB_ABOVE_IDLE = 3.0  # how many dB above idle => "1"
POLL_INTERVAL = 0.02           # how often we read
####################################################


def measure_diff_db(buff):
    """
    Given a block of IQ samples in 'buff', compute:
      center_bin_power - average_of_side_bins
    Returns diff_db or None if glitch frame.
    """
    spectrum = np.fft.fftshift(np.fft.fft(buff * WINDOW))
    power_db = 20 * np.log10(np.abs(spectrum) + 1e-12)
    center_bin = FFT_SIZE // 2
    center_power = power_db[center_bin]

    # Ignore glitch frames
    if center_power < -100:
        return None

    left_side = power_db[center_bin - SIDE_BINS : center_bin]
    right_side = power_db[center_bin+1 : center_bin+1+SIDE_BINS]
    if len(left_side) == 0 or len(right_side) == 0:
        return None

    side_avg = np.mean(np.concatenate([left_side, right_side]))
    return center_power - side_avg


def read_diff_db(sdr, rxStream):
    """
    Read one block of FFT_SIZE from Soapy and compute diff_db.
    Returns diff_db or None on error/short read.
    """
    buff = np.zeros(FFT_SIZE, np.complex64)
    sr = sdr.readStream(rxStream, [buff], FFT_SIZE)
    if sr.ret != FFT_SIZE:
        return None  # error or short read
    return measure_diff_db(buff)


def main():
    # ---- SETUP SDR ----
    sdr = SoapySDR.Device(dict(driver="hackrf"))
    sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
    sdr.setFrequency(SOAPY_SDR_RX, 0, CENTER_FREQ)
    sdr.setGain(SOAPY_SDR_RX, 0, GAIN)
    rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
    sdr.activateStream(rxStream)

    print(f"Tuning to {CENTER_FREQ/1e6:.3f} MHz, measuring idle baseline for {IDLE_MEASURE_DURATION} s...")

    # 1) Measure IDLE baseline
    idle_vals = []
    t0 = time.time()
    while (time.time() - t0) < IDLE_MEASURE_DURATION:
        diff_db = read_diff_db(sdr, rxStream)
        if diff_db is not None:
            idle_vals.append(diff_db)
        time.sleep(POLL_INTERVAL)

    if not idle_vals:
        print("ERROR: No valid baseline readings. Check your device or signals.")
        return

    idle_baseline = np.median(idle_vals)  # or np.mean(idle_vals)
    print(f"Idle baseline (center - side) ≈ {idle_baseline:.2f} dB")

    print("\nNow detecting transitions above baseline...")
    try:
        while True:
            diff_db = read_diff_db(sdr, rxStream)
            if diff_db is None:
                continue

            delta_db = diff_db - idle_baseline
            is_one = (delta_db >= THRESHOLD_DB_ABOVE_IDLE)

            print(f"[{time.strftime('%H:%M:%S')}] diff={diff_db:.2f} dB  Δ={delta_db:.2f} → {'1' if is_one else '0'}")

            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        sdr.deactivateStream(rxStream)
        sdr.closeStream(rxStream)


if __name__ == "__main__":
    main()
