#!/usr/bin/env python3
"""
pyhackrf_scan.py

Requires:
    pip install pyhackrf

This script:
  1) Opens a HackRF device using pyhackrf.
  2) Sets LNA gain=16, VGA gain=32.
  3) Loops over freq_list = [299e6, 300e6, 301e6, 302e6]
  4) For each freq, captures short IQ block, does FFT, prints center amplitude in dB.

Adjust sample_rate, chunk_size, fft_size, etc. as desired.
"""

import time
import numpy as np
from hackrf import HackRF

def main():
    # Frequencies in Hz
    freq_list = [299e6, 300e6, 301e6, 302e6]

    sample_rate = 10e6   # 10 MSPS (HackRF can do up to 20e6)
    lna_gain    = 16     # LNA
    vga_gain    = 32     # VGA
    fft_size    = 8192   # For amplitude measurement
    num_samples = fft_size  # We'll read exactly enough for one FFT

    # Initialize HackRF
    device = HackRF()
    if device.open() != 0:
        print("[ERROR] Could not open HackRF device.")
        return

    # Set sample rate
    ret = device.set_sample_rate(sample_rate)
    if ret != 0:
        print(f"[ERROR] set_sample_rate({sample_rate}) => {ret}")

    # Gains
    device.set_lna_gain(lna_gain)
    device.set_vga_gain(vga_gain)
    # Additional options if supported:
    # device.set_amp_enable(False)  # or True if you want the RF amp

    # We'll store raw IQ in a numpy array after each capture
    # pyhackrf's read() callback-based approach can do this in a blocking call

    def rx_callback(raw_samples, user_data):
        """
        raw_samples: bytes (uint8) => interleaved I,Q.
        user_data: we pass a dict to store samples
        """
        samples_array = np.frombuffer(raw_samples, dtype=np.uint8)
        # Convert from 8-bit signed => HackRF provides 8-bit *unsigned* but
        # the actual hardware data is offset. Typically we do int8 or float.
        # The official hackrf_transfer uses signed int8. Here, let's shift to signed:
        signed = (samples_array.astype(np.int16) - 128).astype(np.int8)
        # Then interleave => complex64
        iq_complex = signed[0::2] + 1j * signed[1::2]

        user_data["samples"] = iq_complex
        user_data["received"] = True
        return 0  # 0 => continue reading

    # Setup device read
    device.start_rx_mode()
    device.add_rx_callback(rx_callback)

    # We'll do a short block capture for each frequency
    for freq in freq_list:
        print(f"\n=== Tuning to {freq/1e6:.3f} MHz ===")

        ret = device.set_freq(int(freq))
        if ret != 0:
            print(f"[ERROR] set_freq({freq}) => {ret}")
            continue

        # Wait a moment for tuning/filters to settle
        time.sleep(0.1)

        # We'll store samples in user_data
        user_data = {"samples": None, "received": False}

        # Request a single chunk
        device.receive_samples(num_samples, user_data)

        # Wait for callback to fill user_data
        timeout = time.time() + 2.0
        while not user_data["received"] and time.time() < timeout:
            time.sleep(0.01)

        if not user_data["received"]:
            print("[WARN] Timed out waiting for samples.")
            continue

        # We have user_data["samples"] => complex64 array of length=fft_size
        iq = user_data["samples"]
        # Apply an FFT window
        window = np.hanning(fft_size)
        spectrum = np.fft.fftshift(np.fft.fft(iq * window))
        mag_db = 20 * np.log10(np.abs(spectrum) + 1e-12)

        center_bin = fft_size // 2
        # If we want just the absolute center bin => mag_db[center_bin]
        # Or we can average e.g. a few bins around center => shape "soft"
        half_bw = 1  # average 1 bin on each side
        band_slice = mag_db[center_bin - half_bw : center_bin + half_bw + 1]
        avg_power = np.mean(band_slice)

        print(f"Freq {freq/1e6:.3f} MHz => center amplitude ~ {avg_power:.2f} dB")

    # Cleanup
    device.remove_rx_callback(rx_callback)
    device.stop_rx_mode()
    device.close()
    print("\n[INFO] Done scanning with pyhackrf.")

if __name__ == "__main__":
    main()
