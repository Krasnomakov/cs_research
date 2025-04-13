#!/usr/bin/env python3
"""
Slow CPU EMF Transmitter
Each bit is 5s: High CPU load for '1', Idle for '0'
Then repeated so the receiver can grab it from a broad CSV sweep.
"""

import threading
import time

MESSAGE_BITS = "1011"  # Example 4-bit message (change as needed)
BIT_DURATION = 5.0     # seconds per bit
REPEAT_GAP   = 2.0     # seconds between repeated transmissions
NUM_THREADS  = 8       # more threads => stronger emission

def busy_loop():
    while True:
        pass  # tight loop => high CPU load => stronger EM

def start_heavy_load():
    stop_event = threading.Event()
    threads = []
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=stress_cpu, args=(stop_event,))
        t.start()
        threads.append(t)
    return stop_event, threads

def stress_cpu(stop_event):
    # Just keep a busy loop while not stopped
    while not stop_event.is_set():
        busy_loop()

def transmit_bit(bit):
    """
    '1' => spawn heavy CPU load for BIT_DURATION
    '0' => do nothing for BIT_DURATION
    """
    if bit == '1':
        stop_event, threads = start_heavy_load()
        time.sleep(BIT_DURATION)
        stop_event.set()
    else:
        # Idle
        time.sleep(BIT_DURATION)

def main():
    print(f"Transmitting bits: {MESSAGE_BITS}")
    while True:
        for bit in MESSAGE_BITS:
            print(f"Sending bit {bit}")
            transmit_bit(bit)
        print("Finished 1 cycle, waiting a bit...")
        time.sleep(REPEAT_GAP)

if __name__ == "__main__":
    main()
