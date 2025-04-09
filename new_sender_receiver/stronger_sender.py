#!/usr/bin/env python3
import threading
import time
import numpy as np

# -------- CONFIG --------
BITSTREAM = "010"          # literal bits
DELAY_ONE = 0.1            # longer '1'
DELAY_ZERO = 0.03
NUM_THREADS = 16           # more than # of cores
ARRAY_SIZE = 200_000       # bigger memory churn
REPEAT_PAUSE = 1.0         # pause after each pattern

def load_cpu_memory(stop_event):
    # Heavier loop
    mat_dim = 400  # NxN
    while not stop_event.is_set():
        mat1 = np.random.randint(0, 255, size=(mat_dim, mat_dim), dtype=np.uint8)
        mat2 = np.random.randint(0, 255, size=(mat_dim, mat_dim), dtype=np.uint8)
        _ = mat1 @ mat2  # matrix multiplication

def start_heavy_threads():
    stop_event = threading.Event()
    threads = []
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=load_cpu_memory, args=(stop_event,))
        t.start()
        threads.append(t)
    return stop_event, threads

def transmit_bitstream(bitstream):
    for bit in bitstream:
        if bit == '1':
            stop_event, threads = start_heavy_threads()
            time.sleep(DELAY_ONE)
            stop_event.set()
            # Wait for all threads to exit
            for t in threads:
                t.join()
        else:
            time.sleep(DELAY_ZERO)

def run_transmitter():
    print("Transmitting bitstream:", BITSTREAM)
    while True:
        transmit_bitstream(BITSTREAM)
        time.sleep(REPEAT_PAUSE)

if __name__ == "__main__":
    run_transmitter()
