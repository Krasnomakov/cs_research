import multiprocessing as mp
import numpy as np
import time
import os

def cpu_stress_worker():
    """
    Heavy CPU + memory load: matrix ops, floating-point math, cache-churn.
    """
    size = 500  # Matrix size; increase if you can
    A = np.random.rand(size, size)
    B = np.random.rand(size, size)
    
    while True:
        # Matrix multiplication (FPU + memory)
        C = np.dot(A, B)

        # Add some non-linear math to hit vector units
        A = np.sin(C) * np.log(C + 1e-5)

        # Optional: Touch more memory
        junk = np.random.bytes(4096)

if __name__ == "__main__":
    cores = os.cpu_count()
    print(f"Starting heavy load on {cores} cores...")

    procs = []
    for _ in range(cores):
        p = mp.Process(target=cpu_stress_worker)
        p.start()
        procs.append(p)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for p in procs:
            p.terminate()
        print("Stopped.")
