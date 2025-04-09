#!/usr/bin/env python3
"""
real_time_listener.py

Continuously read from HackRF at a specified frequency,
perform a short-time FFT on each block, measure amplitude near center,
and print it with a timestamp. Useful for manual correlation
against sender timestamps from stronger_sender.py.

Press Ctrl+C to stop.
"""

import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import numpy as np
import time
import datetime

################### CONFIG ###################
FREQ_HZ = 299e6        # 18 MHz (adjust as needed)
SAMPLE_RATE = 2e6     # 2 MSPS
GAIN = 40
FFT_SIZE = 4096
CENTER_BIN_WIDTH = 1   # how many bins around center to average
PRINT_INTERVAL = 0.1   # seconds between prints (avoid spamming console)
################### CONFIG ###################

def main():
    # 1) Open HackRF via SoapySDR
    print(f"[INFO] Initializing HackRF at {FREQ_HZ/1e6:.3f} MHz, SR={SAMPLE_RATE/1e6:.1f} MSPS")
    sdr = SoapySDR.Device(dict(driver="hackrf"))
    rx_chan = 0
    sdr.setSampleRate(SOAPY_SDR_RX, rx_chan, SAMPLE_RATE)
    sdr.setFrequency(SOAPY_SDR_RX, rx_chan, FREQ_HZ)
    sdr.setGain(SOAPY_SDR_RX, rx_chan, GAIN)

    rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [rx_chan])
    sdr.activateStream(rx_stream)

    window = np.hanning(FFT_SIZE)
    chunk_size = FFT_SIZE

    print("[INFO] Starting continuous reading. Press Ctrl+C to stop.\n")
    last_print = time.time()

    try:
        while True:
            # 2) Read one chunk of samples
            buff = np.empty(chunk_size, np.complex64)
            sr = sdr.readStream(rx_stream, [buff], chunk_size)
            if sr.ret == chunk_size:
                # 3) FFT + amplitude
                spectrum = np.fft.fftshift(np.fft.fft(buff * window))
                mag_db = 20 * np.log10(np.abs(spectrum) + 1e-12)

                center_bin = FFT_SIZE // 2
                half_bw = CENTER_BIN_WIDTH
                band_slice = mag_db[center_bin - half_bw : center_bin + half_bw + 1]
                avg_power = np.mean(band_slice)

                # 4) Print with a timestamp every PRINT_INTERVAL seconds
                now = time.time()
                if (now - last_print) >= PRINT_INTERVAL:
                    now_str = datetime.datetime.now().strftime("%H:%M:%S.%f")
                    print(f"[RX] {now_str} amplitude = {avg_power:.2f} dB")
                    last_print = now

            else:
                # sr.ret < 0 => error, sr.ret < chunk_size => partial read
                # small sleep to avoid busy loop
                time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user.")
    finally:
        sdr.deactivateStream(rx_stream)
        sdr.closeStream(rx_stream)
        print("[INFO] Listener closed.")

if __name__ == "__main__":
    main()
