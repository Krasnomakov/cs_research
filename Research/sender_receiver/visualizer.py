import numpy as np
import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

# SDR Config
CENTER_FREQ = 300e6       # Hz
SAMPLE_RATE = 2e6         # Hz
GAIN = 40                 # dB
FFT_SIZE = 2048           # samples per FFT
READ_COUNT = FFT_SIZE * 2 # read this many samples from stream

# If HackRF returns empty reads N times consecutively, attempt a restart.
zero_frame_threshold = 50

# Setup HackRF
args = dict(driver="hackrf")
sdr = SoapySDR.Device(args)
sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
sdr.setFrequency(SOAPY_SDR_RX, 0, CENTER_FREQ)
sdr.setGain(SOAPY_SDR_RX, 0, GAIN)

rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rxStream)

# Create plot
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
ax.set_xlim(CENTER_FREQ - SAMPLE_RATE/2, CENTER_FREQ + SAMPLE_RATE/2)
ax.set_ylim(-100, 0)
ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Power (dB)")
ax.set_title("Live HackRF Spectrum Visual")

# Buffers
buffs = np.zeros(FFT_SIZE, np.complex64)
freqs = np.fft.fftshift(
    np.fft.fftfreq(FFT_SIZE, 1/SAMPLE_RATE) + CENTER_FREQ
)

# State
consecutive_zero_frames = 0

# Animation update function
def update(frame):
    global consecutive_zero_frames

    sr = sdr.readStream(rxStream, [buffs], READ_COUNT)
    if sr.ret > 0:
        # We only store sr.ret samples in buffs, but the length is up to sr.ret
        # If sr.ret < FFT_SIZE, just fill partial. We'll do a direct FFT anyway.
        # Optionally you can do a window or zero-pad.
        spectrum = np.fft.fftshift(np.fft.fft(buffs))
        power = 10 * np.log10(np.abs(spectrum) + 1e-10)
        line.set_data(freqs, power)
        consecutive_zero_frames = 0
    else:
        consecutive_zero_frames += 1
        print(f"Warning: empty read {consecutive_zero_frames}/{zero_frame_threshold}")
        if consecutive_zero_frames > zero_frame_threshold:
            print("Too many empty reads. Restarting HackRF stream...")
            sdr.deactivateStream(rxStream)
            time.sleep(0.5)
            sdr.activateStream(rxStream)
            consecutive_zero_frames = 0

    return (line,)

ani = animation.FuncAnimation(fig, update, interval=100, blit=True)

# Cleanup on exit
def shutdown():
    print("Shutting down stream.")
    sdr.deactivateStream(rxStream)
    sdr.closeStream(rxStream)

import atexit
atexit.register(shutdown)

plt.show()
