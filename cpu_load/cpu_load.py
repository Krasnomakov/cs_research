import multiprocessing
import time

# Function to perform a CPU-intensive task (e.g., calculating primes)
def cpu_load():
    primes = []
    candidate = 2
    while True:
        is_prime = all(candidate % i != 0 for i in range(2, int(candidate ** 0.5) + 1))
        if is_prime:
            primes.append(candidate)
        candidate += 1

# Run the function on all cores
if __name__ == "__main__":
    # Get the number of available CPU cores
    num_cores = multiprocessing.cpu_count()
    
    # Create a pool of processes to fully load each core
    processes = []
    for _ in range(num_cores):
        p = multiprocessing.Process(target=cpu_load)
        processes.append(p)
        p.start()
    
    # Keep the processes running for a while to monitor the load
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()

