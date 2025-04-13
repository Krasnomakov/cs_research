import numpy as np
import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import time


# Settings
CENTER_FREQ = 300e6       # 300 MHz
SAMPLE_RATE = 2e6         # 2 MS/s
GAIN = 40                 # in dB
CHUNK_SIZE = 2048         # samples per read
FFT_SIZE = 2048
SHOW_BINS = 20            # print these many bins

# Open HackRF device
args = dict(driver="hackrf")
sdr = SoapySDR.Device(args)

# Configure SDR
sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
sdr.setFrequency(SOAPY_SDR_RX, 0, CENTER_FREQ)
sdr.setGain(SOAPY_SDR_RX, 0, GAIN)

# Setup a stream (complex float32)
rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rxStream)

print(f"Listening on {CENTER_FREQ/1e6:.3f} MHz... Press Ctrl+C to stop.")

try:
    while True:
        buffs = np.zeros(CHUNK_SIZE, np.complex64)
        sr = sdr.readStream(rxStream, [buffs], len(buffs))
        if sr.ret > 0:
            # Take FFT of chunk
            spectrum = np.fft.fftshift(np.fft.fft(buffs, n=FFT_SIZE))
            power = 10 * np.log10(np.abs(spectrum) + 1e-10)  # in dB
            center_bin = FFT_SIZE // 2

            # Get center region
            region = power[center_bin - SHOW_BINS//2 : center_bin + SHOW_BINS//2]
            freqs = np.linspace(CENTER_FREQ - SAMPLE_RATE/2, CENTER_FREQ + SAMPLE_RATE/2, FFT_SIZE)
            focus_freqs = freqs[center_bin - SHOW_BINS//2 : center_bin + SHOW_BINS//2]
            print(" | ".join(f"{f/1e6:.2f}MHz: {p:.1f}dB" for f, p in zip(focus_freqs, region)))
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Stopping...")
finally:
    sdr.deactivateStream(rxStream)
    sdr.closeStream(rxStream)

