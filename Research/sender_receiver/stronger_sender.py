#!/usr/bin/env python3
"""
EMF CPU+Memory Load Transmitter for Raspberry Pi
Generates stronger emission sidebands in ~300 MHz region by heavy CPU + memory churn.
"""

import threading
import time
import numpy as np
import os

# -------- CONFIG --------
MESSAGE = "Hello"
PREAMBLE = "10101010"
DELAY_ONE = 0.03  # Increase 'on' time for a stronger, more detectable burst
DELAY_ZERO = 0.03
NUM_THREADS = 8   # More than # of cores
ARRAY_SIZE = 10_000  # For memory-churn array
REPEAT_PAUSE = 0.5  # Pause between repeated transmissions

def text_to_bitstream(msg):
    # Convert to bits with a leading preamble
    return PREAMBLE + ''.join(f'{ord(c):08b}' for c in msg)

def load_cpu_memory(stop_event):
    """
    Hefty load: run big matrix ops (random * random)
    to stress CPU + memory.
    """
    # Pre-allocate arrays once outside loop
    arr1 = np.random.randint(0, 255, size=(ARRAY_SIZE,), dtype=np.uint8)
    arr2 = np.random.randint(0, 255, size=(ARRAY_SIZE,), dtype=np.uint8)
    while not stop_event.is_set():
        # e.g. sum product, or other ops
        _ = np.dot(arr1, arr2)  # 1D dot product
        # You can also do arr1 * arr2 in a loop, etc.

def start_heavy_threads():
    """
    Spawn multiple heavy-load threads, pinned if desired.
    """
    stop_event = threading.Event()
    threads = []
    for i in range(NUM_THREADS):
        t = threading.Thread(target=load_cpu_memory, args=(stop_event,))
        t.start()
        threads.append(t)
    return stop_event, threads

def transmit_bitstream(bitstream):
    for bit in bitstream:
        if bit == '1':
            # Start heavy load
            stop_event, threads = start_heavy_threads()
            time.sleep(DELAY_ONE)
            stop_event.set()
        else:
            # idle
            time.sleep(DELAY_ZERO)

def run_transmitter():
    bitstream = text_to_bitstream(MESSAGE)
    print("Transmitting bitstream:", bitstream)
    while True:
        transmit_bitstream(bitstream)
        time.sleep(REPEAT_PAUSE)

if __name__ == "__main__":
    run_transmitter()
