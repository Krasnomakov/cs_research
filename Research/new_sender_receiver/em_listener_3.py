#!/usr/bin/env python3
import SoapySDR
from SoapySDR import *
import numpy as np
import time

CENTER_FREQ = 299.8e6      # Adjust to exact observed spike
SAMPLE_RATE = 2e6
FFT_SIZE = 8192
GAIN = 40
SIDE_BINS = 5
THRESHOLD_DB = 1.0  # or 0.5 if your spike is small
WINDOW = np.hanning(FFT_SIZE)

sdr = SoapySDR.Device(dict(driver="hackrf"))
sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
sdr.setFrequency(SOAPY_SDR_RX, 0, CENTER_FREQ)
sdr.setGain(SOAPY_SDR_RX, 0, GAIN)

rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rxStream)
print(f"Listening near {CENTER_FREQ/1e6:.3f} MHz...")

try:
    while True:
        buff = np.zeros(FFT_SIZE, np.complex64)
        sr = sdr.readStream(rxStream, [buff], FFT_SIZE)
        if sr.ret != FFT_SIZE:
            # skip partial/failed reads
            continue

        spectrum = np.fft.fftshift(np.fft.fft(buff * WINDOW))
        power_db = 20 * np.log10(np.abs(spectrum) + 1e-12)

        center_bin = FFT_SIZE // 2
        center_power = power_db[center_bin]

        # Avoid glitch frames that show -240
        if center_power < -100:
            continue

        # Average side bins
        left_side = power_db[center_bin - SIDE_BINS : center_bin]
        right_side = power_db[center_bin+1 : center_bin+1+SIDE_BINS]
        if len(left_side) == 0 or len(right_side) == 0:
            continue

        side_avg = np.mean(np.concatenate([left_side, right_side]))
        diff_db = center_power - side_avg

        is_one = diff_db > THRESHOLD_DB

        print(f"[{time.strftime('%H:%M:%S')}] C={center_power:.2f}dB S={side_avg:.2f}dB diff={diff_db:.2f} → {'1' if is_one else '0'}")

        time.sleep(0.05)

except KeyboardInterrupt:
    print("Stopping...")

sdr.deactivateStream(rxStream)
sdr.closeStream(rxStream)
