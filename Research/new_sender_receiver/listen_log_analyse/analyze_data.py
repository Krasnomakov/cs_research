#!/usr/bin/env python3
"""
analyze_data.py
Loads raw interleaved float32 IQ from captured_data.iq,
performs FFT, plots or detects CPU load sidebands, etc.
"""

import numpy as np
import matplotlib.pyplot as plt

INFILE = "captured_data.iq"
SAMPLE_RATE = 2e6

# Load interleaved float32: I, Q, I, Q...
raw = np.fromfile(INFILE, dtype=np.float32)
# Reshape as complex
raw_complex = raw.view(np.complex64)

print(f"Loaded {raw_complex.size} IQ samples.")

# For a quick spectrum (one FFT):
N = 65536
if raw_complex.size < N:
    N = raw_complex.size

window = np.hanning(N)
spectrum = np.fft.fftshift(np.fft.fft(raw_complex[:N] * window))
power_db = 20 * np.log10(np.abs(spectrum) + 1e-12)

freq_axis = np.linspace(-SAMPLE_RATE/2, SAMPLE_RATE/2, N)

plt.plot(freq_axis/1e6, power_db)
plt.xlabel("Frequency (MHz relative)")
plt.ylabel("Power (dB)")
plt.title("Captured Spectrum around 20 MHz")
plt.grid(True)
plt.show()
