#!/usr/bin/env python3
import threading
import time
import numpy as np

# -------- CONFIG --------
BITSTREAM = "010"         # literal, not ascii
DELAY_ONE = 0.03          # duration for bit '1'
DELAY_ZERO = 0.03         # duration for bit '0'
NUM_THREADS = 8           # stress CPU
ARRAY_SIZE = 10_000       # memory churn
REPEAT_PAUSE = 0.5        # delay after full pattern

def load_cpu_memory(stop_event):
    arr1 = np.random.randint(0, 255, size=(ARRAY_SIZE,), dtype=np.uint8)
    arr2 = np.random.randint(0, 255, size=(ARRAY_SIZE,), dtype=np.uint8)
    while not stop_event.is_set():
        _ = np.dot(arr1, arr2)

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
        else:
            time.sleep(DELAY_ZERO)

def run_transmitter():
    print("Transmitting bitstream:", BITSTREAM)
    while True:
        transmit_bitstream(BITSTREAM)
        time.sleep(REPEAT_PAUSE)

if __name__ == "__main__":
    run_transmitter()
