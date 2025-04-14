import numpy as np
import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

########################
# SDR Config
########################
CENTER_FREQ = 300e6       # Hz
SAMPLE_RATE = 1e6         # Hz  (lower than before)
GAIN        = 40          # dB
FFT_SIZE    = 1024        # smaller than 2048
READ_COUNT  = 1024        # reduce chunk size

########################
# Setup HackRF
########################
args = dict(driver="hackrf")
sdr = SoapySDR.Device(args)
sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
sdr.setFrequency(SOAPY_SDR_RX, 0, CENTER_FREQ)
sdr.setGain(SOAPY_SDR_RX, 0, GAIN)

rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rxStream)

########################
# Matplotlib Plot Setup
########################
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)

# Frequency axis
freqs = np.fft.fftshift(np.fft.fftfreq(FFT_SIZE, 1/SAMPLE_RATE) + CENTER_FREQ)

#ax.set_xlim(CENTER_FREQ - SAMPLE_RATE/2, CENTER_FREQ + SAMPLE_RATE/2)
ZOOM_SPAN_HZ = 200e3  # 200 kHz total span
ax.set_xlim(CENTER_FREQ - ZOOM_SPAN_HZ / 2, CENTER_FREQ + ZOOM_SPAN_HZ / 2)

ax.set_ylim(-100, 0)
ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Power (dB)")
ax.set_title("HackRF Spectrum (Light Version)")

# Buffers
buffs = np.zeros(FFT_SIZE, np.complex64)

# For readStream empty read detection
zero_frame_threshold = 50
consecutive_zero_frames = 0

def update(frame):
    global consecutive_zero_frames

    sr = sdr.readStream(rxStream, [buffs], READ_COUNT)
    if sr.ret > 0:
        # sr.ret samples are read into buffs
        # If sr.ret < FFT_SIZE, we can zero-pad the remainder
        if sr.ret < FFT_SIZE:
            # zero out leftover
            buffs[sr.ret:] = 0 + 0j

        spectrum = np.fft.fftshift(np.fft.fft(buffs))
        power = 10 * np.log10(np.abs(spectrum) + 1e-10)
        line.set_data(freqs, power)
        consecutive_zero_frames = 0
    else:
        consecutive_zero_frames += 1
        print(f"Warning: empty read {consecutive_zero_frames}/{zero_frame_threshold}")
        if consecutive_zero_frames > zero_frame_threshold:
            print("Too many empty reads—restarting stream.")
            sdr.deactivateStream(rxStream)
            time.sleep(0.5)
            sdr.activateStream(rxStream)
            consecutive_zero_frames = 0

    return (line,)

ani = animation.FuncAnimation(fig, update, interval=100, blit=True)

def shutdown():
    print("Shutting down stream.")
    sdr.deactivateStream(rxStream)
    sdr.closeStream(rxStream)

import atexit
atexit.register(shutdown)

plt.show()
