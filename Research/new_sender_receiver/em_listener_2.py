import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import numpy as np
import time

# -------- CONFIG --------
CENTER_FREQ = 300e6        # Hz
SAMPLE_RATE = 2e6          # Hz (small focus)
FFT_SIZE = 8192            # narrow spikes
GAIN = 40
THRESHOLD_DB = 3.0         # dB above sliding baseline
WINDOW = np.hanning(FFT_SIZE)
SLIDING_WINDOW = 20        # past N values to average baseline
CENTER_BIN_WIDTH = 1       # number of FFT bins to average (center-only)

# -------- SETUP SDR --------
sdr = SoapySDR.Device(dict(driver="hackrf"))
sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
sdr.setFrequency(SOAPY_SDR_RX, 0, CENTER_FREQ)
sdr.setGain(SOAPY_SDR_RX, 0, GAIN)

rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rxStream)

# -------- INIT --------
power_history = []
print("Listening at 300 MHz...")

try:
    while True:
        # Read block of samples
        buff = np.array([0]*FFT_SIZE, np.complex64)
        sr = sdr.readStream(rxStream, [buff], FFT_SIZE)
        if sr.ret != FFT_SIZE:
            print("Read failed:", sr.ret)
            continue

        # FFT
        spectrum = np.fft.fftshift(np.fft.fft(buff * WINDOW))
        power_db = 20 * np.log10(np.abs(spectrum) + 1e-12)

        center_bin = FFT_SIZE // 2
        band = power_db[center_bin - CENTER_BIN_WIDTH : center_bin + CENTER_BIN_WIDTH + 1]
        avg_power = np.mean(band)

        power_history.append(avg_power)
        if len(power_history) > SLIDING_WINDOW:
            power_history.pop(0)

        baseline = np.mean(power_history)
        delta = avg_power - baseline
        is_one = delta >= THRESHOLD_DB

        print(f"[{time.strftime('%H:%M:%S')}] Power: {avg_power:.2f} dB (Δ {delta:.2f}) → {'1' if is_one else '0'}")

        time.sleep(0.02)  # faster polling

except KeyboardInterrupt:
    print("Stopping...")
    sdr.deactivateStream(rxStream)
    sdr.closeStream(rxStream)
