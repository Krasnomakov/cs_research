import numpy as np
import matplotlib.pyplot as plt

# Load IQ file (interleaved int8: I, Q, I, Q...)
raw = np.fromfile('samples.iq', dtype=np.int8)

# Convert to complex: I + jQ
iq = raw[::2] + 1j * raw[1::2]

# Plot spectrum
N = 1024 * 64  # FFT size
window = np.hanning(N)
spectrum = np.fft.fftshift(np.fft.fft(iq[:N] * window))
power = 20 * np.log10(np.abs(spectrum))

# Frequency axis
f_axis = np.linspace(-5, 5, N)  # MHz if you used -s 10e6

plt.figure()
plt.plot(f_axis, power)
plt.title("Captured Spectrum at 299 MHz")
plt.xlabel("Frequency (MHz relative to center)")
plt.ylabel("Power (dB)")
plt.grid(True)
plt.show()
