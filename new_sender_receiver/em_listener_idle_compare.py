import SoapySDR
from SoapySDR import *
import numpy as np
import time

################## CONFIG ##################
CENTER_FREQ = 299.8e6
SAMPLE_RATE = 2e6
FFT_SIZE = 8192
GAIN = 40

SIDE_BINS = 5
WINDOW = np.hanning(FFT_SIZE)
THRESHOLD_DB_ABOVE_IDLE = 2.0  # if signal is >2dB above idle, call it "1"
###########################################

def measure_power_centered(sdr):
    """ Read a block, compute center-vs-side difference. Returns diff_db. """
    buff = np.zeros(FFT_SIZE, np.complex64)
    sr = sdr.readStream(rxStream, [buff], FFT_SIZE)
    if sr.ret != FFT_SIZE:
        return None

    spectrum = np.fft.fftshift(np.fft.fft(buff * WINDOW))
    power_db = 20 * np.log10(np.abs(spectrum) + 1e-12)
    center_bin = FFT_SIZE // 2
    center_power = power_db[center_bin]

    # Avoid glitch frames
    if center_power < -100:
        return None

    # Compare to side bins
    left_side = power_db[center_bin - SIDE_BINS : center_bin]
    right_side = power_db[center_bin+1 : center_bin+1+SIDE_BINS]
    if len(left_side) == 0 or len(right_side) == 0:
        return None
    side_avg = np.mean(np.concatenate([left_side, right_side]))

    diff_db = center_power - side_avg
    return diff_db

# ------ SETUP SDR ------
sdr = SoapySDR.Device(dict(driver="hackrf"))
sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
sdr.setFrequency(SOAPY_SDR_RX, 0, CENTER_FREQ)
sdr.setGain(SOAPY_SDR_RX, 0, GAIN)

rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rxStream)

print(f"Center = {CENTER_FREQ/1e6:.3f} MHz, measuring IDLE baseline...")

# 1) Measure IDLE baseline for ~3 seconds
t_start = time.time()
idle_vals = []
while time.time() - t_start < 3.0:  # 3s of idle
    diff_db = measure_power_centered(sdr)
    if diff_db is not None:
        idle_vals.append(diff_db)
    time.sleep(0.02)

if len(idle_vals) == 0:
    print("ERROR: No valid baseline readings!")
    sdr.deactivateStream(rxStream)
    sdr.closeStream(rxStream)
    exit()

idle_baseline = np.median(idle_vals)  # or mean
print(f"IDLE baseline diff ~ {idle_baseline:.2f} dB")

print("Now listening for changes above idle baseline...\n")
try:
    while True:
        diff_db = measure_power_centered(sdr)
        if diff_db is None:
            continue
        delta = diff_db - idle_baseline

        is_one = (delta >= THRESHOLD_DB_ABOVE_IDLE)

        print(f"[{time.strftime('%H:%M:%S')}] diff={diff_db:.2f}dB vs. idle (Δ {delta:.2f}) → {'1' if is_one else '0'}")
        time.sleep(0.02)

except KeyboardInterrupt:
    print("Stopping...")
sdr.deactivateStream(rxStream)
sdr.closeStream(rxStream)
