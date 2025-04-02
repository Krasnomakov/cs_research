#!/usr/bin/env python3
"""
Real-time CPU EMF listener using GNU Radio + HackRF
Tune to a certain frequency (e.g. 300 MHz) and measure amplitude.
We then poll the amplitude every ~0.2s and print if it's above/below threshold.
"""

import time
import numpy as np

from gnuradio import gr, blocks, analog
import osmosdr

#############################
# Configuration
#############################
CENTER_FREQ = 300e6      # e.g. 300 MHz
SAMPLE_RATE = 2e6        # e.g. 2 MS/s
GAIN        = 40         # HackRF gain, adjust as needed
THRESHOLD   = 1e-5       # power threshold for 'HIGH vs LOW' - tune to your environment
POLL_INTERVAL = 0.2      # seconds

#############################
# GNU Radio Flowgraph
#############################
class CPULoadDetector(gr.top_block):
    def __init__(self, center_freq, samp_rate, gain):
        gr.top_block.__init__(self, "CPU EMF Detector")

        # Source: HackRF (through gr-osmosdr)
        self.source = osmosdr.source(args="hackrf=0")
        self.source.set_sample_rate(samp_rate)
        self.source.set_center_freq(center_freq)
        self.source.set_gain(gain)
        self.source.set_antenna("RX")

        # Convert complex IQ -> power (magnitude squared)
        self.mag_sq = blocks.complex_to_mag_squared(1)

        # Smooth it out with a Moving Average
        avg_len = 4096       # the number of samples to average over
        avg_scale = 1.0 / avg_len
        self.mavg = blocks.moving_average_ff(avg_len, avg_scale, 4000, True)

        # This probe lets us read the amplitude from Python
        self.probe = analog.probe_avg_mag_sqrd_cf(0, 1e-2)  
        # (params are hold_time, alpha; can be tweaked)

        # Connect it all:
        # HackRF -> mag_sq -> mavg -> probe
        self.connect(self.source, self.mag_sq, self.mavg, self.probe)

    def get_power_level(self):
        # Returns the average power (float)
        return self.probe.level()

#############################
# Main: run flowgraph, poll amplitude
#############################
def main():
    tb = CPULoadDetector(CENTER_FREQ, SAMPLE_RATE, GAIN)
    tb.start()  # start flowgraph (runs in background)

    print("Listening at %.3f MHz. Press Ctrl+C to stop." % (CENTER_FREQ/1e6))
    try:
        while True:
            avg_power = tb.get_power_level()
            # Compare to threshold
            state = "HIGH" if avg_power > THRESHOLD else "LOW"
            print(f"Power={avg_power:.2e} => {state}")
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping flowgraph...")
    tb.stop()
    tb.wait()

if __name__ == "__main__":
    main()
