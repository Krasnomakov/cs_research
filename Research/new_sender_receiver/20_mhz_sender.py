#!/usr/bin/env python3
"""
sender.py
Toggles CPU load on/off to create an EM side-channel at ~20 MHz.
'1' = heavy CPU load, '0' = idle.
"""

import multiprocessing
import time

def cpu_load():
    """
    Very heavy infinite prime search loop to stress CPU.
    """
    candidate = 2
    while True:
        # Quick primality check
        is_prime = all(candidate % i != 0 for i in range(2, int(candidate**0.5)+1))
        if is_prime:
            pass  # We don't even store them, just churn
        candidate += 1

def start_load(num_cores=None):
    """
    Spawn multiple processes to fully load CPU cores.
    :param num_cores: If None, use all CPU cores. Otherwise, use requested number.
    :return: list of processes
    """
    if num_cores is None:
        num_cores = multiprocessing.cpu_count()
    processes = []
    for _ in range(num_cores):
        p = multiprocessing.Process(target=cpu_load)
        p.start()
        processes.append(p)
    return processes

def stop_load(processes):
    """
    Terminate prime-search processes, ensuring CPU goes idle.
    """
    for p in processes:
        p.terminate()
    for p in processes:
        p.join()

def main():
    """
    Continuously toggle CPU load:
      5s ON => heavy load
      5s OFF => idle
    Adjust durations as desired.
    """
    print("Toggling CPU load on/off every 5 seconds.")
    processes = []
    while True:
        # '1' => start heavy load
        print("State=1: Starting CPU load.")
        processes = start_load()  # use all cores
        time.sleep(5)

        # '0' => kill the load for idle
        print("State=0: Stopping CPU load.")
        stop_load(processes)
        time.sleep(5)

if __name__ == "__main__":
    main()

