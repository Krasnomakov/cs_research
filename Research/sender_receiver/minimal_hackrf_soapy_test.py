import numpy as np
import SoapySDR
from SoapySDR import *
import time

SR = 1e6
FREQ = 300e6
GAIN = 40
N = 1024

args = dict(driver="hackrf")
sdr = SoapySDR.Device(args)
sdr.setSampleRate(SOAPY_SDR_RX, 0, SR)
sdr.setFrequency(SOAPY_SDR_RX, 0, FREQ)
sdr.setGain(SOAPY_SDR_RX, 0, GAIN)

rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rxStream)

buff = np.zeros(N, np.complex64)

for i in range(10):  # just 10 reads
    sr = sdr.readStream(rxStream, [buff], len(buff))
    if sr.ret > 0:
        fft_vals = np.fft.fftshift(np.fft.fft(buff))
        power = 10 * np.log10(np.abs(fft_vals) + 1e-10)
        print(f"FFT power sample: min={power.min():.1f}dB, max={power.max():.1f}dB")
    else:
        print("Empty read")
    time.sleep(0.2)

sdr.deactivateStream(rxStream)
sdr.closeStream(rxStream)
print("Done.")
