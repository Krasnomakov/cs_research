import numpy as np
import matplotlib.pyplot as plt

FILE = 'samples_10s.iq'
SAMPLE_RATE = 10_000_000
FFT_SIZE = 16384  # Balance between resolution & CPU

# Load only part of the file
raw = np.fromfile(FILE, dtype=np.int8, count=2*FFT_SIZE)
iq = raw[::2] + 1j * raw[1::2]

# Window + FFT
window = np.hanning(FFT_SIZE)
spectrum = np.fft.fftshift(np.fft.fft(iq * window))
power = 20 * np.log10(np.abs(spectrum) + 1e-12)
freq_axis = np.linspace(-SAMPLE_RATE/2, SAMPLE_RATE/2, FFT_SIZE) / 1e6

# Plot
plt.plot(freq_axis, power)
plt.title("Single FFT Slice (Centered @ 299 MHz)")
plt.xlabel("Frequency (MHz relative)")
plt.ylabel("Power (dB)")
plt.grid(True)
plt.show()
