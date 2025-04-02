import threading
import os
import time
import ctypes
import signal

# --- Config ---
MESSAGE = "Hello"
BITS_PER_CHAR = 8
PREAMBLE = "10101010"
DELAY_ONE = 0.01   # seconds of load for bit '1'
DELAY_ZERO = 0.01  # seconds of idle for bit '0'
NUM_THREADS = 4    # how many CPU stress threads to use

def text_to_bitstream(msg):
    return PREAMBLE + ''.join(f'{ord(c):08b}' for c in msg)

# --- Busy loop (generates EM load) ---
def busy_loop():
    while True:
        pass

# --- Worker that stresses the CPU ---
def stress_cpu(stop_event):
    while not stop_event.is_set():
        busy_loop()

# --- Thread starter ---
def start_stress_threads():
    threads = []
    stop_event = threading.Event()
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=stress_cpu, args=(stop_event,))
        t.start()
        threads.append(t)
    return stop_event, threads

# --- Main transmitter logic ---
def transmit_bitstream(bitstream):
    for bit in bitstream:
        if bit == '1':
            stop_event, threads = start_stress_threads()
            time.sleep(DELAY_ONE)
            stop_event.set()
        else:
            time.sleep(DELAY_ZERO)

# --- Entry Point ---
def run_transmitter():
    bitstream = text_to_bitstream(MESSAGE)
    print(f"Sending bitstream: {bitstream}")
    while True:
        transmit_bitstream(bitstream)
        time.sleep(0.5)  # gap between repeats

if __name__ == '__main__':
    run_transmitter()
