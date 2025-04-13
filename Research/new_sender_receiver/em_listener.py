import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import numpy as np
import time

# ---- CONFIG ----
CENTER_FREQ = 300e6   # Hz
SAMPLE_RATE = 2e6     # Hz (small to focus on narrowband)
GAIN = 40             # dB
FFT_SIZE = 2048
PEAK_THRESHOLD_DB = 8  # above baseline to count as '1'
WINDOW = np.hanning(FFT_SIZE)

# ---- SETUP SDR ----
sdr = SoapySDR.Device(dict(driver="hackrf"))
sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
sdr.setFrequency(SOAPY_SDR_RX, 0, CENTER_FREQ)
sdr.setGain(SOAPY_SDR_RX, 0, GAIN)

rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rxStream)

# ---- BASELINE INIT ----
print("Calibrating baseline power...")
baseline_db = None

try:
    while True:
        # Allocate buffer
        buff = np.array([0]*FFT_SIZE, np.complex64)
        sr = sdr.readStream(rxStream, [buff], FFT_SIZE)

        if sr.ret != FFT_SIZE:
            print("Read failed:", sr.ret)
            continue

        # FFT
        spectrum = np.fft.fftshift(np.fft.fft(buff * WINDOW))
        power_db = 20 * np.log10(np.abs(spectrum) + 1e-12)

        # Use center bin or average around it
        center_bin = FFT_SIZE // 2
        band = power_db[center_bin - 5:center_bin + 5]
        avg_power = np.mean(band)

        if baseline_db is None:
            baseline_db = avg_power
            print(f"[Baseline] {baseline_db:.2f} dB")
            continue

        delta = avg_power - baseline_db
        detected = delta > PEAK_THRESHOLD_DB

        print(f"[{time.strftime('%H:%M:%S')}] Power: {avg_power:.1f} dB (Δ {delta:.1f}) → {'1' if detected else '0'}")

        time.sleep(0.05)

except KeyboardInterrupt:
    print("Stopping...")

sdr.deactivateStream(rxStream)
sdr.closeStream(rxStream)
