#!/usr/bin/env python3
"""
listen_data_logger.py
Capture raw IQ data from HackRF (SoapySDR) at a chosen frequency & sample rate,
then save it to a file for offline analysis.
"""

import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import numpy as np
import time
import sys

######################## CONFIG ########################
OUTPUT_FILE = "captured_data.iq"   # Output filename
FREQ_HZ = 20e6                     # 20 MHz (adjust as desired)
SAMPLE_RATE = 2e6                  # 2 MSPS
GAIN = 40                          # HackRF gain
CAPTURE_SECS = 5.0                 # How many seconds to capture
########################################################

def main():
    # ----- Setup SoapySDR (HackRF) -----
    try:
        sdr = SoapySDR.Device(dict(driver="hackrf"))
    except Exception as e:
        print(f"Error opening SDR device: {e}")
        sys.exit(1)

    rx_chan = 0
    sdr.setSampleRate(SOAPY_SDR_RX, rx_chan, SAMPLE_RATE)
    sdr.setFrequency(SOAPY_SDR_RX, rx_chan, FREQ_HZ)
    sdr.setGain(SOAPY_SDR_RX, rx_chan, GAIN)

    # We'll use CF32 (complex float32) format
    rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [rx_chan])
    sdr.activateStream(rx_stream)

    print(f"Capturing {CAPTURE_SECS} seconds at {SAMPLE_RATE/1e6} MSPS, freq={FREQ_HZ/1e6} MHz")

    # Number of samples to capture in total
    total_samps = int(CAPTURE_SECS * SAMPLE_RATE)

    # We can read in chunks
    chunk_size = 8192
    out_data = np.empty(2 * total_samps, dtype=np.float32)  
    # ^ We'll store real & imag interleaved: I0, Q0, I1, Q1, ...

    idx = 0
    start_time = time.time()

    # We'll keep reading until we have 'total_samps' samples
    while idx < (2 * total_samps):
        buff = np.empty(chunk_size, np.complex64)
        sr = sdr.readStream(rx_stream, [buff], chunk_size)
        if sr.ret > 0:
            # Convert complex64 → interleaved float32
            n = sr.ret
            # Make sure we don't overshoot final array
            needed = (2 * total_samps) - idx
            num_float32 = 2 * n   # each complex sample => 2 float32

            # Slice out only as much as needed to fill out_data
            used = min(needed, num_float32)

            # Buff as real-imag float32
            re = buff[:n].real.astype(np.float32)
            im = buff[:n].imag.astype(np.float32)

            # Interleave
            interleaved = np.empty(2*n, dtype=np.float32)
            interleaved[0::2] = re
            interleaved[1::2] = im

            out_data[idx : idx+used] = interleaved[:used]
            idx += used
        else:
            print(f"readStream returned {sr.ret}, flags={sr.flags}")
            if sr.ret == SOAPY_SDR_TIMEOUT:
                # Possibly no data ready
                time.sleep(0.01)
            elif sr.ret < 0:
                print("Stream error, exiting...")
                break

        if (time.time() - start_time) > (CAPTURE_SECS + 2):
            print("Capture took too long, exiting.")
            break

    # Deactivate & close stream
    sdr.deactivateStream(rx_stream)
    sdr.closeStream(rx_stream)

    # Truncate out_data if we overshot
    if idx < len(out_data):
        out_data = out_data[:idx]

    # Save to file
    print(f"Writing {len(out_data)//2} IQ samples to {OUTPUT_FILE}")
    out_data.tofile(OUTPUT_FILE)

    print("Done.")

if __name__ == "__main__":
    main()
